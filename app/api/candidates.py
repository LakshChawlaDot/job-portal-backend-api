from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import ApplicationStatus, JobStatus, UserRole
from app.db.session import get_db
from app.dependencies import require_roles
from app.models import Application, CandidateProfile, Job, SavedJob, User
from app.schemas import ApplicationCreate, ApplicationRead, JobRead, ProfileCreate, ProfileRead
from app.services.email import send_application_submitted
from app.services.skills import get_or_create_skills

router = APIRouter(prefix="/candidate", tags=["candidate"])
UPLOAD_DIR = Path("uploads/resumes")


@router.put("/profile", response_model=ProfileRead)
def upsert_profile(
    payload: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CANDIDATE)),
) -> CandidateProfile:
    profile = db.scalar(
        select(CandidateProfile)
        .where(CandidateProfile.user_id == current_user.id)
        .options(selectinload(CandidateProfile.skills))
    )
    if not profile:
        profile = CandidateProfile(user_id=current_user.id)
        db.add(profile)
    profile.headline = payload.headline
    profile.bio = payload.bio
    profile.location = payload.location
    profile.experience_years = payload.experience_years
    profile.skills = get_or_create_skills(db, payload.skills)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/profile/resume", response_model=ProfileRead)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CANDIDATE)),
) -> CandidateProfile:
    if file.content_type not in {"application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume must be PDF or Word")
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    if not profile:
        profile = CandidateProfile(user_id=current_user.id)
        db.add(profile)
        db.flush()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "resume").suffix
    target = UPLOAD_DIR / f"user-{current_user.id}{suffix}"
    target.write_bytes(file.file.read())
    profile.resume_path = str(target)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/jobs/{job_id}/apply", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def apply_to_job(
    job_id: int,
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CANDIDATE)),
) -> Application:
    job = db.get(Job, job_id)
    if not job or job.status != JobStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active job not found")
    existing = db.scalar(select(Application).where(Application.job_id == job_id, Application.candidate_id == current_user.id))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already applied to this job")
    application = Application(
        job_id=job_id,
        candidate_id=current_user.id,
        cover_letter=payload.cover_letter,
        status=ApplicationStatus.SUBMITTED.value,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    send_application_submitted(current_user.email, job.title)
    return application


@router.post("/jobs/{job_id}/save", status_code=status.HTTP_201_CREATED)
def save_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CANDIDATE)),
) -> dict[str, str]:
    if not db.get(Job, job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    saved = db.get(SavedJob, {"job_id": job_id, "candidate_id": current_user.id})
    if not saved:
        db.add(SavedJob(job_id=job_id, candidate_id=current_user.id))
        db.commit()
    return {"message": "Job saved"}


@router.get("/applications", response_model=list[ApplicationRead])
def application_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CANDIDATE)),
) -> list[Application]:
    return db.scalars(select(Application).where(Application.candidate_id == current_user.id)).all()


@router.get("/saved-jobs", response_model=list[JobRead])
def saved_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CANDIDATE)),
) -> list[Job]:
    return db.scalars(
        select(Job)
        .join(SavedJob, SavedJob.job_id == Job.id)
        .where(SavedJob.candidate_id == current_user.id)
        .options(selectinload(Job.skills))
    ).all()

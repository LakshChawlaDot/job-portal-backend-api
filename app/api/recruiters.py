from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import ApplicationStatus, UserRole
from app.db.session import get_db
from app.dependencies import require_roles
from app.models import Application, Company, Job, User
from app.schemas import ApplicationRead, ApplicationStatusUpdate, CompanyCreate, CompanyRead, JobCreate, JobRead, JobUpdate
from app.services.email import send_application_status
from app.services.skills import get_or_create_skills

router = APIRouter(prefix="/recruiter", tags=["recruiter"])


@router.post("/companies", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.RECRUITER)),
) -> Company:
    company = Company(**payload.model_dump(), owner_id=current_user.id)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def _owned_job_or_404(db: Session, job_id: int, recruiter_id: int) -> Job:
    job = db.scalar(select(Job).where(Job.id == job_id, Job.recruiter_id == recruiter_id).options(selectinload(Job.skills)))
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post("/jobs", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def post_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.RECRUITER)),
) -> Job:
    company = db.get(Company, payload.company_id)
    if not company or company.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    data = payload.model_dump(exclude={"skills"})
    job = Job(**data, recruiter_id=current_user.id)
    job.skills = get_or_create_skills(db, payload.skills)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.patch("/jobs/{job_id}", response_model=JobRead)
def update_job(
    job_id: int,
    payload: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.RECRUITER)),
) -> Job:
    job = _owned_job_or_404(db, job_id, current_user.id)
    data = payload.model_dump(exclude_unset=True, exclude={"skills"})
    for field, value in data.items():
        setattr(job, field, value)
    if payload.skills is not None:
        job.skills = get_or_create_skills(db, payload.skills)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.RECRUITER)),
) -> None:
    job = _owned_job_or_404(db, job_id, current_user.id)
    db.delete(job)
    db.commit()


@router.get("/jobs/{job_id}/applicants", response_model=list[ApplicationRead])
def view_applicants(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.RECRUITER)),
) -> list[Application]:
    _owned_job_or_404(db, job_id, current_user.id)
    return db.scalars(select(Application).where(Application.job_id == job_id)).all()


@router.patch("/applications/{application_id}", response_model=ApplicationRead)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.RECRUITER)),
) -> Application:
    if payload.status not in {ApplicationStatus.SHORTLISTED, ApplicationStatus.REJECTED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only shortlist or reject is allowed here")
    application = db.scalar(
        select(Application)
        .join(Job)
        .where(Application.id == application_id, Job.recruiter_id == current_user.id)
        .options(selectinload(Application.job), selectinload(Application.candidate))
    )
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    application.status = payload.status.value
    db.commit()
    db.refresh(application)
    send_application_status(application.candidate.email, application.job.title, application.status)
    return application

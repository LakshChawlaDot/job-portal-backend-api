from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Date, cast, desc, func, select
from sqlalchemy.orm import Session

from app.core.enums import JobStatus, UserRole
from app.db.session import get_db
from app.dependencies import require_roles
from app.models import Application, Company, Job, JobSkill, Skill, User
from app.schemas import AnalyticsRead, CompanyRead, JobRead, UserRead

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead])
def manage_users(db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN))) -> list[User]:
    return db.scalars(select(User).order_by(User.created_at.desc())).all()


@router.patch("/users/{user_id}/active", response_model=UserRead)
def set_user_active(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/companies", response_model=list[CompanyRead])
def manage_companies(db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN))) -> list[Company]:
    return db.scalars(select(Company).order_by(Company.created_at.desc())).all()


@router.patch("/companies/{company_id}/approve", response_model=CompanyRead)
def approve_company(
    company_id: int,
    is_approved: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> Company:
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    company.is_approved = is_approved
    db.commit()
    db.refresh(company)
    return company


@router.get("/jobs", response_model=list[JobRead])
def moderate_jobs(db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN))) -> list[Job]:
    return db.scalars(select(Job).order_by(Job.created_at.desc())).all()


@router.patch("/jobs/{job_id}/status", response_model=JobRead)
def set_job_status(
    job_id: int,
    job_status: JobStatus,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    job.status = job_status.value
    db.commit()
    db.refresh(job)
    return job


@router.get("/analytics", response_model=AnalyticsRead)
def dashboard_analytics(db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN))) -> dict:
    since = datetime.now(UTC) - timedelta(days=30)
    apps_by_day = db.execute(
        select(cast(Application.created_at, Date).label("day"), func.count(Application.id))
        .where(Application.created_at >= since)
        .group_by("day")
        .order_by("day")
    ).all()
    top_skills = db.execute(
        select(Skill.name, func.count(Job.id).label("uses"))
        .join(JobSkill, JobSkill.skill_id == Skill.id)
        .join(Job, Job.id == JobSkill.job_id)
        .group_by(Skill.id)
        .order_by(desc("uses"))
        .limit(10)
    ).all()
    return {
        "total_users": db.scalar(select(func.count(User.id))) or 0,
        "active_jobs": db.scalar(select(func.count(Job.id)).where(Job.status == JobStatus.ACTIVE.value)) or 0,
        "applications_per_day": [{"day": str(day), "count": count} for day, count in apps_by_day],
        "top_skills": [{"skill": name, "count": count} for name, count in top_skills],
    }

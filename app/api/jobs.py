from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import JobStatus, JobType
from app.db.session import get_db
from app.models import Job, Skill
from app.schemas import JobRead

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobRead])
def search_jobs(
    keyword: str | None = None,
    location: str | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    experience: int | None = None,
    skills: list[str] | None = None,
    job_type: JobType | None = None,
    db: Session = Depends(get_db),
) -> list[Job]:
    query = select(Job).where(Job.status == JobStatus.ACTIVE.value).options(selectinload(Job.skills))

    if keyword:
        pattern = f"%{keyword}%"
        query = query.where(or_(Job.title.ilike(pattern), Job.description.ilike(pattern)))
    if location:
        query = query.where(Job.location.ilike(f"%{location}%"))
    if salary_min is not None:
        query = query.where(or_(Job.salary_max.is_(None), Job.salary_max >= salary_min))
    if salary_max is not None:
        query = query.where(or_(Job.salary_min.is_(None), Job.salary_min <= salary_max))
    if experience is not None:
        query = query.where(
            and_(
                or_(Job.experience_min.is_(None), Job.experience_min <= experience),
                or_(Job.experience_max.is_(None), Job.experience_max >= experience),
            )
        )
    if job_type:
        query = query.where(Job.job_type == job_type.value)
    if skills:
        normalized = [skill.strip().lower() for skill in skills if skill.strip()]
        if normalized:
            query = query.join(Job.skills).where(Skill.name.in_(normalized)).group_by(Job.id)

    return db.scalars(query.order_by(Job.created_at.desc())).all()


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job

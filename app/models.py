from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ApplicationStatus, JobStatus, JobType, UserRole
from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default=UserRole.CANDIDATE.value, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    candidate_profile: Mapped["CandidateProfile"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    companies: Mapped[List["Company"]] = relationship(back_populates="owner")
    jobs: Mapped[List["Job"]] = relationship(back_populates="recruiter")
    applications: Mapped[List["Application"]] = relationship(back_populates="candidate")
    saved_jobs: Mapped[List["SavedJob"]] = relationship(back_populates="candidate")


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    website: Mapped[str] = mapped_column(String(255), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    owner: Mapped["User"] = relationship(back_populates="companies")
    jobs: Mapped[List["Job"]] = relationship(back_populates="company")


class CandidateProfile(Base, TimestampMixin):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    headline: Mapped[str] = mapped_column(String(255), nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    resume_path: Mapped[str] = mapped_column(String(500), nullable=True)

    user: Mapped["User"] = relationship(back_populates="candidate_profile")
    skills: Mapped[List["Skill"]] = relationship(
        secondary="candidate_skills",
        back_populates="candidate_profiles",
    )


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    candidate_profiles: Mapped[List["CandidateProfile"]] = relationship(
        secondary="candidate_skills",
        back_populates="skills",
    )
    jobs: Mapped[List["Job"]] = relationship(
        secondary="job_skills",
        back_populates="skills",
    )


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    candidate_profile_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), primary_key=True)


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    salary_min: Mapped[int] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int] = mapped_column(Integer, nullable=True)
    experience_min: Mapped[int] = mapped_column(Integer, nullable=True)
    experience_max: Mapped[int] = mapped_column(Integer, nullable=True)
    job_type: Mapped[str] = mapped_column(String(50), default=JobType.FULL_TIME.value, index=True)
    status: Mapped[str] = mapped_column(String(50), default=JobStatus.ACTIVE.value, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    recruiter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    company: Mapped["Company"] = relationship(back_populates="jobs")
    recruiter: Mapped["User"] = relationship(back_populates="jobs")
    skills: Mapped[List["Skill"]] = relationship(
        secondary="job_skills",
        back_populates="jobs",
    )
    applications: Mapped[List["Application"]] = relationship(back_populates="job")
    saved_by: Mapped[List["SavedJob"]] = relationship(back_populates="job")


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), primary_key=True)


class Application(Base, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="uq_application_job_candidate"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(50), default=ApplicationStatus.SUBMITTED.value, index=True)
    cover_letter: Mapped[str] = mapped_column(Text, nullable=True)

    job: Mapped["Job"] = relationship(back_populates="applications")
    candidate: Mapped["User"] = relationship(back_populates="applications")


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped["Job"] = relationship(back_populates="saved_by")
    candidate: Mapped["User"] = relationship(back_populates="saved_jobs")

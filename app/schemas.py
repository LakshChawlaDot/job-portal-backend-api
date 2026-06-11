from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import ApplicationStatus, JobStatus, JobType, UserRole


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole = UserRole.CANDIDATE


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class SkillRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ProfileCreate(BaseModel):
    headline: str | None = None
    bio: str | None = None
    location: str | None = None
    experience_years: int = 0
    skills: list[str] = []


class ProfileRead(BaseModel):
    id: int
    headline: str | None
    bio: str | None
    location: str | None
    experience_years: int
    resume_path: str | None
    skills: list[SkillRead] = []

    model_config = ConfigDict(from_attributes=True)


class CompanyCreate(BaseModel):
    name: str
    description: str | None = None
    website: str | None = None
    location: str | None = None


class CompanyRead(CompanyCreate):
    id: int
    owner_id: int
    is_approved: bool

    model_config = ConfigDict(from_attributes=True)


class JobCreate(BaseModel):
    title: str
    description: str
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    job_type: JobType = JobType.FULL_TIME
    status: JobStatus = JobStatus.ACTIVE
    company_id: int
    skills: list[str] = []


class JobUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    job_type: JobType | None = None
    status: JobStatus | None = None
    skills: list[str] | None = None


class JobRead(BaseModel):
    id: int
    title: str
    description: str
    location: str | None
    salary_min: int | None
    salary_max: int | None
    experience_min: int | None
    experience_max: int | None
    job_type: JobType
    status: JobStatus
    company_id: int
    recruiter_id: int
    skills: list[SkillRead] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationCreate(BaseModel):
    cover_letter: str | None = None


class ApplicationRead(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    status: ApplicationStatus
    cover_letter: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class AnalyticsRead(BaseModel):
    total_users: int
    active_jobs: int
    applications_per_day: list[dict[str, int | str]]
    top_skills: list[dict[str, int | str]]

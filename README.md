# Job Portal Backend API

FastAPI backend for a job portal with JWT authentication, refresh tokens, RBAC, candidate/recruiter/admin workflows, job search, email notification hooks, and analytics.

## Tech Stack

- FastAPI
- SQLAlchemy 2.0
- Alembic
- JWT auth with refresh tokens
- Pytest
- Optional Celery + Redis background tasks

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

API docs are available at `http://127.0.0.1:8000/docs`.

## Tests

```bash
pytest
```

## Default Roles

- `candidate`
- `recruiter`
- `admin`

The first admin can be promoted directly in the database or created by a seed script you add for your deployment.

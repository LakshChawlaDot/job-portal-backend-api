from fastapi import FastAPI

from app.api import admin, auth, candidates, jobs, recruiters
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(candidates.router)
app.include_router(recruiters.router)
app.include_router(admin.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}

from fastapi import APIRouter

from app.api.v1.endpoints.resume import (
    router as resume_router
)

api_router = APIRouter()

api_router.include_router(
    resume_router,
    prefix="/resumes",
    tags=["Resumes"]
)
from app.api.v1.endpoints.job import (
    router as job_router
)

api_router.include_router(
    job_router,
    prefix="/jobs",
    tags=["Jobs"]
)
from fastapi import APIRouter

from app.api.v1.endpoints.resume import router as resume_router
from app.api.v1.endpoints.job import router as job_router
from app.api.v1.endpoints.ai import router as ai_router
from app.api.v1.endpoints.ml import router as ml_router

from app.api.v1.endpoints.candidate import (
    router as candidate_router
)

api_router = APIRouter()

api_router.include_router(
    candidate_router,
    prefix="/candidates",
    tags=["Candidates"]
)

api_router.include_router(
    ai_router,
    prefix="/ai",
    tags=["AI Intelligence"],
)

api_router.include_router(
    ml_router,
    prefix="/ml",
    tags=["ML Evaluation"],
)

api_router.include_router(
    resume_router,
    prefix="/resumes",
    tags=["Resumes"]
)

api_router.include_router(
    job_router,
    prefix="/jobs",
    tags=["Jobs"]
)

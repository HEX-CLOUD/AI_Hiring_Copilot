from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.ai import AIRecruiterBriefRequest, AIRecruiterBriefResponse, AIReindexResponse, AIStatusResponse, AIRuntimeCheckResponse, AIWarmupResponse
from app.services.ai_retrieval_service import AIRetrievalService
from app.services.vector_search_service import VectorSearchService


router = APIRouter()


@router.post("/recruiter-brief", response_model=AIRecruiterBriefResponse)
def create_recruiter_brief(
    request: AIRecruiterBriefRequest,
    db: Session = Depends(get_db),
):
    return AIRetrievalService.build_recruiter_brief(
        db,
        request.query,
        request.limit,
        request.generate,
    )


@router.post("/reindex", response_model=AIReindexResponse)
def reindex_candidate_profiles(db: Session = Depends(get_db)):
    return VectorSearchService.sync_candidates(db)


@router.get("/status", response_model=AIStatusResponse)
def get_ai_status():
    return VectorSearchService.status()


@router.get("/runtime-check", response_model=AIRuntimeCheckResponse)
def get_ai_runtime_check():
    return VectorSearchService.runtime_check()


@router.post("/warmup", response_model=AIWarmupResponse)
def warm_ai_runtime(background_tasks: BackgroundTasks):
    background_tasks.add_task(VectorSearchService.warmup)
    return {"status": "warming"}

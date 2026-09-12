from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status

from sqlalchemy.orm import Session

from app.db.dependencies import get_db

from app.services.candidate_service import (
    CandidateService
)
from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.schemas.candidate import (
    CandidateCreate,
    CandidateDBResponse,
    CandidateUpdate
)
from app.schemas.match import CandidateJobMatchResponse

router = APIRouter()


@router.post(
    "/",
    response_model=CandidateDBResponse,
    status_code=status.HTTP_201_CREATED
)
def create_candidate(
    candidate: CandidateCreate,
    db: Session = Depends(get_db)
):
    result = CandidateService.create(
        db,
        candidate
    )

    if not result["created"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return CandidateService._serialize_candidate(
        result["candidate"]
    )


@router.get(
    "/",
    response_model=list[CandidateDBResponse]
)
def get_candidates(
    skills: str | None = Query(default=None),
    min_experience: int | None = Query(default=None, ge=0),
    max_experience: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db)
):

    return CandidateService.get_all_candidates(
        db,
        skills=skills,
        min_experience=min_experience,
        max_experience=max_experience
    )


@router.get(
    "/search",
    response_model=list[CandidateDBResponse]
)
def search_candidates(
    q: str = Query(min_length=1),
    db: Session = Depends(get_db)
):
    return CandidateService.search(
        db,
        q
    )


@router.get(
    "/{candidate_id}/jobs",
    response_model=list[CandidateJobMatchResponse]
)
def rank_jobs_for_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    candidate = CandidateService.get_model_by_id(
        db,
        candidate_id
    )

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

    return MatchingService.rank_jobs_for_candidate(
        JobService.get_all(db),
        candidate
    )


@router.get(
    "/{candidate_id}",
    response_model=CandidateDBResponse
)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    candidate = CandidateService.get_by_id(
        db,
        candidate_id
    )

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

    return candidate


@router.patch(
    "/{candidate_id}",
    response_model=CandidateDBResponse
)
def update_candidate(
    candidate_id: int,
    candidate: CandidateUpdate,
    db: Session = Depends(get_db)
):
    result = CandidateService.update(
        db,
        candidate_id,
        candidate
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

    if not result["updated"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return CandidateService._serialize_candidate(
        result["candidate"]
    )


@router.put(
    "/{candidate_id}",
    response_model=CandidateDBResponse
)
def replace_candidate(
    candidate_id: int,
    candidate: CandidateUpdate,
    db: Session = Depends(get_db)
):
    return update_candidate(
        candidate_id,
        candidate,
        db
    )


@router.delete(
    "/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    deleted = CandidateService.delete(
        db,
        candidate_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

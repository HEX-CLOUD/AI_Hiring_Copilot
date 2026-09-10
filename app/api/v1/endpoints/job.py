from fastapi import APIRouter

from app.services.matching_service import (
    MatchingService
)

from app.schemas.job import (
    JobMatchResponse
)

router = APIRouter()


@router.post(
    "/match",
    response_model=JobMatchResponse
)
async def match_job():

    candidate_skills = [
        "Python",
        "FastAPI",
        "Docker",
        "PostgreSQL"
    ]

    jd_skills = [
        "Python",
        "FastAPI",
        "Docker",
        "AWS",
        "PostgreSQL"
    ]

    return MatchingService.match_skills(
        candidate_skills,
        jd_skills
    )
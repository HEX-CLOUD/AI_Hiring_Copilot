from pydantic import BaseModel


class JobMatchResponse(BaseModel):
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
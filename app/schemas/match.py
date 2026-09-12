from pydantic import BaseModel


class JobCandidateMatchRequest(BaseModel):
    job_id: int


class CandidateJobMatchResponse(BaseModel):
    candidate_id: int
    candidate_name: str
    job_id: int
    job_title: str | None = None
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    candidate_experience: int | None = None
    required_experience: int | None = None
    experience_match: bool
    fit_explanation: str

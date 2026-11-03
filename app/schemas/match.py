from pydantic import BaseModel


class JobCandidateMatchRequest(BaseModel):
    job_id: int


class ScoreComponentResponse(BaseModel):
    signal: str
    weight: float
    raw_score: float | None = None
    contribution: float
    description: str


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
    score_breakdown: list[ScoreComponentResponse]
    fairness_note: str
    fit_explanation: str


class CandidateJobInsightResponse(CandidateJobMatchResponse):
    candidate_summary: str
    strengths: list[str]
    weaknesses: list[str]
    hiring_recommendation: str
    recommendation_reason: str

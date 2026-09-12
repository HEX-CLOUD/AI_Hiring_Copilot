from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CandidateExtractResponse(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = Field(default_factory=list)


class CandidateCreate(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    years_experience: int | None = Field(default=None, ge=0)
    skills: list[str] = Field(default_factory=list)
    resume_path: str | None = None


class CandidateUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    years_experience: int | None = Field(default=None, ge=0)
    skills: list[str] | None = None
    resume_path: str | None = None


class CandidateDBResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    phone: str | None = None
    years_experience: int | None = None
    skills: list[str] = Field(default_factory=list)
    resume_path: str | None = None
    created_at: datetime
    updated_at: datetime


class CandidateUploadResponse(BaseModel):
    created: bool
    message: str
    candidate: CandidateDBResponse | None = None


class CandidateSearchResponse(CandidateDBResponse):
    relevance_score: float
    matched_terms: list[str] = Field(default_factory=list)
    search_explanation: str

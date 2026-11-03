from datetime import datetime
from typing import Literal
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
    education: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    work_history: list[str] = Field(default_factory=list)
    source_text: str | None = None
    extraction_metadata: dict = Field(default_factory=dict)
    pipeline_stage: Literal["new", "reviewing", "shortlisted", "interview", "rejected"] = "new"
    recruiter_notes: str | None = None


class CandidateUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    years_experience: int | None = Field(default=None, ge=0)
    skills: list[str] | None = None
    resume_path: str | None = None
    education: list[str] | None = None
    projects: list[str] | None = None
    certifications: list[str] | None = None
    work_history: list[str] | None = None
    source_text: str | None = None
    extraction_metadata: dict | None = None
    pipeline_stage: Literal["new", "reviewing", "shortlisted", "interview", "rejected"] | None = None
    recruiter_notes: str | None = None


class CandidateDBResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    phone: str | None = None
    years_experience: int | None = None
    skills: list[str] = Field(default_factory=list)
    resume_path: str | None = None
    education: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    work_history: list[str] = Field(default_factory=list)
    source_text: str | None = None
    extraction_metadata: dict = Field(default_factory=dict)
    pipeline_stage: str = "new"
    recruiter_notes: str | None = None
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

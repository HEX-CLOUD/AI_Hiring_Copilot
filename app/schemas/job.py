from datetime import datetime

from pydantic import BaseModel
from pydantic import Field


class JobCreate(BaseModel):
    title: str | None = None
    description: str | None = None
    min_experience: int | None = Field(default=None, ge=0)
    skills: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)


class JobUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    min_experience: int | None = Field(default=None, ge=0)
    skills: list[str] | None = None
    requirements: list[str] | None = None


class JobResponse(BaseModel):
    id: int
    title: str | None = None
    description: str | None = None
    min_experience: int | None = None
    skills: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobExtractResponse(JobResponse):
    pass


class JobMatchResponse(BaseModel):
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    experience_match: bool
    fit_explanation: str

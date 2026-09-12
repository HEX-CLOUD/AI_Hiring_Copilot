from datetime import datetime
from pydantic import BaseModel, Field


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
    id: int
    full_name: str
    email: str
    phone: str | None = None
    years_experience: int | None = None
    skills: list[str] = Field(default_factory=list)
    resume_path: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CandidateUploadResponse(BaseModel):
    created: bool
    message: str
    candidate: CandidateDBResponse | None = None

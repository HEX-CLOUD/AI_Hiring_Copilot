from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


DecisionStatus = Literal["shortlisted", "interview", "rejected"]


class CandidateJobDecisionUpdate(BaseModel):
    decision: DecisionStatus
    notes: str | None = None


class CandidateJobDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: int
    job_id: int
    decision: DecisionStatus
    notes: str | None = None
    updated_at: datetime

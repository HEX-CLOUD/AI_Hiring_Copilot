from pydantic import BaseModel, Field


class RankingModelStatusResponse(BaseModel):
    trained: bool
    training_samples: int = 0
    trained_at: str | None = None
    feature_names: list[str] = Field(default_factory=list)
    feature_importances: dict[str, float] = Field(default_factory=dict)
    metrics: dict[str, float | None] = Field(default_factory=dict)
    training_data_source: str = "recruiter decisions"
    minimum_samples_required: int


class RankingTrainingResponse(RankingModelStatusResponse):
    message: str


class RankingDatasetRecord(BaseModel):
    candidate_id: int
    job_id: int
    decision: str
    label: float
    features: dict[str, float]

from pydantic import BaseModel, Field

from app.schemas.candidate import CandidateSearchResponse


class AIRecruiterBriefRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=5, ge=1, le=10)
    generate: bool = False


class AIRecruiterBriefResponse(BaseModel):
    answer: str
    retrieval_method: str
    grounding_note: str
    semantic_retrieval_active: bool
    generation_mode: str
    generated_with_model: str | None = None
    source_candidate_ids: list[int] = Field(default_factory=list)
    retrieval_latency_ms: float
    index_sync: dict[str, int]
    interpreted_filters: dict
    sources: list[CandidateSearchResponse]


class AIReindexResponse(BaseModel):
    indexed: int
    unchanged: int = 0
    removed: int = 0
    total: int = 0
    model: str


class AIStatusResponse(BaseModel):
    embedding_model: str
    vector_store: str
    last_error: str | None = None
    ollama_configured: bool
    ollama_model: str
    ollama_reachable: bool = False
    ollama_model_available: bool = False


class AIRuntimeCheckResponse(AIStatusResponse):
    semantic_retrieval_ready: bool
    generation_ready: bool


class AIWarmupResponse(BaseModel):
    status: str

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./ai_hiring.db"
    CHROMA_PERSIST_DIRECTORY: str = "./artifacts/rag_vector_store"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    # The demo ships with MiniLM downloaded locally. Avoid Hugging Face network
    # retries during a presentation; set this to false only when intentionally
    # downloading/updating the embedding model.
    EMBEDDING_LOCAL_ONLY: bool = True
    SEMANTIC_MIN_RELEVANCE_SCORE: float = 35.0
    OLLAMA_BASE_URL: str | None = None
    OLLAMA_MODEL: str = "phi3:mini"
    OLLAMA_TIMEOUT_SECONDS: int = 30
    OLLAMA_MAX_TOKENS: int = 350
    RANKING_MODEL_PATH: str = "./artifacts/ml_models/ranking_model.joblib"
    RANKING_MIN_TRAINING_SAMPLES: int = 6

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()

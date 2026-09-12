from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine

from app.models.candidate import Candidate
from app.models.job import Job

Base.metadata.create_all(bind=engine)

from app.api.v1.router import api_router

app = FastAPI(
    title="AI Hiring Copilot",
    version="1.0.0"
)

app.include_router(
    api_router,
    prefix="/api/v1"
)


@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Hiring Copilot"
    }
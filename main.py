from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.base import Base
from app.db.session import engine

from app.models.candidate import Candidate
from app.models.job import Job

Base.metadata.create_all(bind=engine)

from app.api.v1.router import api_router

app = FastAPI(
    title="TalentIQ AI Hiring Intelligence",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router,
    prefix="/api/v1"
)


@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "TalentIQ AI Hiring Intelligence"
    }

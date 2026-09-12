import os

os.environ["DATABASE_URL"] = "sqlite:///./test_ai_hiring.db"

from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.dependencies import get_db
from app.db.session import SessionLocal, engine
from main import app


def override_get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db


def teardown_module():
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_candidate_job_matching_scores_skills_and_experience():
    client = TestClient(app)

    candidate_response = client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "API Test Candidate",
            "email": "api-test-candidate@example.com",
            "years_experience": 3,
            "skills": ["Python", "FastAPI", "Docker"],
        },
    )
    assert candidate_response.status_code == 201

    job_response = client.post(
        "/api/v1/jobs/",
        json={
            "title": "Backend Engineer",
            "description": "Build APIs with Python, FastAPI, Docker, and PostgreSQL.",
            "min_experience": 4,
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            "requirements": [
                "4+ years experience",
                "Python and FastAPI API development",
            ],
        },
    )
    assert job_response.status_code == 201

    job_id = job_response.json()["id"]

    match_response = client.post(
        "/api/v1/jobs/match",
        json={"job_id": job_id},
    )
    assert match_response.status_code == 200

    matches = match_response.json()

    assert len(matches) == 1
    assert matches[0]["candidate_name"] == "API Test Candidate"
    assert matches[0]["match_score"] == 60
    assert matches[0]["matched_skills"] == ["Python", "FastAPI", "Docker"]
    assert matches[0]["missing_skills"] == ["PostgreSQL"]
    assert matches[0]["experience_match"] is False

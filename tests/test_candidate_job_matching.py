import os
import uuid
from io import BytesIO
from pathlib import Path

import pytest
os.environ["DATABASE_URL"] = "sqlite:///./test_ai_hiring.db"

from docx import Document
from fastapi.testclient import TestClient

from app.api.v1.endpoints import job as job_endpoint
from app.api.v1.endpoints import resume as resume_endpoint
from app.db.base import Base
from app.db.dependencies import get_db
from app.db.session import SessionLocal, engine
from app.services.extraction_service import ExtractionService
from app.core.config import settings
from app.services.vector_search_service import VectorSearchService
from main import app


@pytest.fixture(autouse=True)
def disable_local_generation_for_tests(monkeypatch):
    """Keep endpoint tests deterministic even when a local Ollama model exists."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", None)


def build_docx_bytes(lines):
    document = Document()

    for line in lines:
        document.add_paragraph(line)

    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)

    return buffer.getvalue()


def make_upload_dir(name):
    path = Path("tests") / "_tmp_uploads" / name / uuid.uuid4().hex
    path.mkdir(parents=True)

    return path


def override_get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def setup_module():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db


def teardown_module():
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


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


def test_duplicate_candidate_email_returns_conflict():
    client = TestClient(app)
    payload = {
        "full_name": "Duplicate Candidate",
        "email": "duplicate@example.com",
        "years_experience": 2,
        "skills": ["Python"],
    }

    first_response = client.post("/api/v1/candidates/", json=payload)
    second_response = client.post("/api/v1/candidates/", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Candidate already exists"


def test_candidate_filters_by_skills_and_experience():
    client = TestClient(app)

    client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "Backend Candidate",
            "email": "backend@example.com",
            "years_experience": 5,
            "skills": ["Python", "FastAPI", "Docker"],
        },
    )
    client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "Frontend Candidate",
            "email": "frontend@example.com",
            "years_experience": 1,
            "skills": ["JavaScript"],
        },
    )

    response = client.get(
        "/api/v1/candidates/?skills=python,fastapi&min_experience=2"
    )

    assert response.status_code == 200
    candidates = response.json()

    assert len(candidates) == 1
    assert candidates[0]["full_name"] == "Backend Candidate"


def test_candidate_pipeline_stage_and_notes_can_be_updated_and_filtered():
    client = TestClient(app)
    created = client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "Pipeline Candidate",
            "email": "pipeline@example.com",
            "skills": ["Python"],
        },
    )

    assert created.status_code == 201
    candidate_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/candidates/{candidate_id}",
        json={
            "pipeline_stage": "shortlisted",
            "recruiter_notes": "Strong API fundamentals. Confirm stakeholder experience.",
        },
    )

    assert updated.status_code == 200
    assert updated.json()["pipeline_stage"] == "shortlisted"
    assert updated.json()["recruiter_notes"].startswith("Strong API")

    filtered = client.get("/api/v1/candidates/?pipeline_stage=shortlisted")
    assert filtered.status_code == 200
    assert [candidate["id"] for candidate in filtered.json()] == [candidate_id]


def test_matching_rewards_experience_when_requirement_is_met():
    client = TestClient(app)

    client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "Senior Candidate",
            "email": "senior@example.com",
            "years_experience": 6,
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
        },
    )
    job_response = client.post(
        "/api/v1/jobs/",
        json={
            "title": "Senior Backend Engineer",
            "description": "Build APIs with Python and FastAPI.",
            "min_experience": 4,
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            "requirements": ["4+ years experience"],
        },
    )

    match_response = client.post(
        "/api/v1/jobs/match",
        json={"job_id": job_response.json()["id"]},
    )

    assert match_response.status_code == 200
    match = match_response.json()[0]

    assert match["match_score"] == 100
    assert match["experience_match"] is True


def test_matching_returns_explainable_score_breakdown_and_fairness_note():
    client = TestClient(app)
    candidate = client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "Explainable Candidate",
            "email": "explainable@example.com",
            "years_experience": 5,
            "skills": ["Python", "FastAPI"],
        },
    ).json()
    job = client.post(
        "/api/v1/jobs/",
        json={
            "title": "Explainable Backend Role",
            "min_experience": 4,
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        },
    ).json()

    response = client.get(f"/api/v1/jobs/{job['id']}/candidates")
    match = next(item for item in response.json() if item["candidate_id"] == candidate["id"])

    assert response.status_code == 200
    assert match["match_score"] == 60
    assert match["score_breakdown"] == [
        {
            "signal": "Required skill coverage",
            "weight": 80,
            "raw_score": 50,
            "contribution": 40,
            "description": "Matched 2 of 4 required skills.",
        },
        {
            "signal": "Experience requirement",
            "weight": 20,
            "raw_score": 100,
            "contribution": 20,
            "description": "Meets the 4+ years requirement.",
        },
    ]
    assert "not an automated hiring decision" in match["fairness_note"]


def test_ai_runtime_check_exposes_local_model_readiness_contract():
    client = TestClient(app)
    response = client.get("/api/v1/ai/runtime-check")

    assert response.status_code == 200
    payload = response.json()
    assert payload["embedding_model"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert payload["vector_store"] == "ChromaDB"
    assert isinstance(payload["generation_ready"], bool)


def test_ai_warmup_endpoint_acknowledges_background_model_warmup(monkeypatch):
    monkeypatch.setattr(VectorSearchService, "warmup", lambda: None)
    client = TestClient(app)

    response = client.post("/api/v1/ai/warmup")

    assert response.status_code == 200
    assert response.json() == {"status": "warming"}


def test_ranking_model_training_rejects_insufficient_recruiter_labels():
    client = TestClient(app)

    response = client.post("/api/v1/ml/ranking/train")

    assert response.status_code == 400
    assert "At least 6 labelled recruiter decisions" in response.json()["detail"]


def test_ai_brief_reports_deterministic_generation_when_no_local_llm(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", None)
    client = TestClient(app)
    client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "RAG Fallback Candidate",
            "email": "rag-fallback@example.com",
            "skills": ["Python"],
        },
    )

    response = client.post(
        "/api/v1/ai/recruiter-brief",
        json={"query": "python", "generate": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["generation_mode"] == "deterministic-grounded-summary"
    assert payload["generated_with_model"] is None
    assert payload["source_candidate_ids"]


def test_semantic_relevance_gate_rejects_weak_matches_without_query_evidence():
    assert settings.SEMANTIC_MIN_RELEVANCE_SCORE == 35.0
    assert not VectorSearchService.is_result_relevant(31, [])
    assert not VectorSearchService.is_result_relevant(12, [])
    assert VectorSearchService.is_result_relevant(60, [])
    assert VectorSearchService.is_result_relevant(12, ["python"])


def test_job_description_extraction_helpers():
    text = (
        "Senior Backend Engineer\n"
        "Must have 4+ years experience with Python, FastAPI and Docker.\n"
        "Required knowledge of PostgreSQL.\n"
    )

    assert ExtractionService.extract_years_experience(text) == 4
    assert ExtractionService.extract_skills(text) == [
        "Python",
        "FastAPI",
        "Docker",
        "PostgreSQL",
    ]
    assert ExtractionService.extract_requirements(text) == [
        "Must have 4+ years experience with Python, FastAPI and Docker.",
        "Required knowledge of PostgreSQL.",
    ]


def test_resume_structured_profile_extracts_research_fields():
    text = (
        "Candidate Name\n"
        "Education\n"
        "B.Tech Computer Science, MIT Manipal\n"
        "Projects\n"
        "TalentIQ candidate ranking platform\n"
        "Certifications\n"
        "AWS Cloud Practitioner\n"
        "Work Experience\n"
        "Backend Engineer at Example Labs\n"
    )

    profile = ExtractionService.extract_structured_profile(text)

    assert profile["education"] == ["B.Tech Computer Science, MIT Manipal"]
    assert profile["projects"] == ["TalentIQ candidate ranking platform"]
    assert profile["certifications"] == ["AWS Cloud Practitioner"]
    assert profile["work_history"] == ["Backend Engineer at Example Labs"]
    assert profile["metadata"]["parser"] == "heuristic-v1"


def test_candidate_response_exposes_structured_profile_fields():
    client = TestClient(app)

    response = client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "Structured Candidate",
            "email": "structured@example.com",
            "skills": ["Python"],
            "education": ["B.Tech Computer Science"],
            "projects": ["TalentIQ"],
            "certifications": ["AWS Cloud Practitioner"],
            "work_history": ["Backend Engineer"],
            "extraction_metadata": {"parser": "test"},
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["education"] == ["B.Tech Computer Science"]
    assert payload["projects"] == ["TalentIQ"]
    assert payload["certifications"] == ["AWS Cloud Practitioner"]
    assert payload["work_history"] == ["Backend Engineer"]
    assert payload["extraction_metadata"] == {"parser": "test"}


def test_semantic_candidate_search_ranks_relevant_candidates():
    client = TestClient(app)

    client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "API Backend Candidate",
            "email": "api-backend@example.com",
            "years_experience": 4,
            "skills": ["Python", "FastAPI", "Docker"],
        },
    )
    client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "Frontend Candidate",
            "email": "frontend-search@example.com",
            "years_experience": 2,
            "skills": ["JavaScript"],
        },
    )

    response = client.get(
        "/api/v1/candidates/semantic-search?q=python fastapi docker"
    )

    assert response.status_code == 200
    results = response.json()

    assert len(results) == 1
    assert results[0]["full_name"] == "API Backend Candidate"
    assert results[0]["relevance_score"] == 100
    assert results[0]["matched_terms"] == ["docker", "fastapi", "python"]


def test_semantic_candidate_search_respects_limit():
    client = TestClient(app)

    for index in range(3):
        client.post(
            "/api/v1/candidates/",
            json={
                "full_name": f"Python Candidate {index}",
                "email": f"python-candidate-{index}@example.com",
                "years_experience": index + 1,
                "skills": ["Python"],
            },
        )

    response = client.get(
        "/api/v1/candidates/semantic-search?q=python&limit=2"
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_ai_retrieval_brief_returns_grounded_candidate_evidence():
    client = TestClient(app)
    client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "AI Retrieval Candidate",
            "email": "ai-retrieval@example.com",
            "skills": ["Python"],
            "projects": ["Built a retrieval augmented hiring assistant"],
        },
    )

    response = client.post(
        "/api/v1/ai/recruiter-brief",
        json={"query": "retrieval augmented python"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sources"][0]["full_name"] == "AI Retrieval Candidate"
    assert payload["source_candidate_ids"]
    assert payload["answer"]
    assert payload["grounding_note"]


def test_candidate_job_insights_recommend_strong_fit():
    client = TestClient(app)

    candidate_response = client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "Insight Strong Candidate",
            "email": "insight-strong@example.com",
            "years_experience": 6,
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
        },
    )
    job_response = client.post(
        "/api/v1/jobs/",
        json={
            "title": "Senior Backend Engineer",
            "description": "Build APIs with Python, FastAPI, Docker, and PostgreSQL.",
            "min_experience": 4,
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            "requirements": ["4+ years experience"],
        },
    )

    response = client.get(
        "/api/v1/jobs/"
        f"{job_response.json()['id']}/candidates/"
        f"{candidate_response.json()['id']}/insights"
    )

    assert response.status_code == 200
    insight = response.json()

    assert insight["match_score"] == 100
    assert insight["hiring_recommendation"] == "Strong recommend"
    assert "Meets the minimum experience requirement" in insight["strengths"]
    assert insight["weaknesses"] == [
        "No major gaps found from the available data"
    ]


def test_candidate_job_insights_warn_on_partial_fit():
    client = TestClient(app)

    candidate_response = client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "Insight Partial Candidate",
            "email": "insight-partial@example.com",
            "years_experience": 2,
            "skills": ["Python"],
        },
    )
    job_response = client.post(
        "/api/v1/jobs/",
        json={
            "title": "Backend Engineer",
            "description": "Build APIs with Python, FastAPI and PostgreSQL.",
            "min_experience": 4,
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "requirements": ["4+ years experience"],
        },
    )

    response = client.get(
        "/api/v1/jobs/"
        f"{job_response.json()['id']}/candidates/"
        f"{candidate_response.json()['id']}/insights"
    )

    assert response.status_code == 200
    insight = response.json()

    assert insight["hiring_recommendation"] == "Not recommended"
    assert "FastAPI" in insight["weaknesses"][0]
    assert "minimum experience" in insight["weaknesses"][1]


def test_job_candidate_decision_is_saved_and_updated():
    client = TestClient(app)
    candidate = client.post(
        "/api/v1/candidates/",
        json={
            "full_name": "Decision Candidate",
            "email": "decision@example.com",
            "skills": ["Python"],
        },
    ).json()
    job = client.post(
        "/api/v1/jobs/",
        json={"title": "Decision Role", "skills": ["Python"]},
    ).json()

    first = client.put(
        f"/api/v1/jobs/{job['id']}/candidates/{candidate['id']}/decision",
        json={"decision": "shortlisted", "notes": "Strong technical alignment."},
    )
    second = client.put(
        f"/api/v1/jobs/{job['id']}/candidates/{candidate['id']}/decision",
        json={"decision": "interview", "notes": "Schedule a technical conversation."},
    )
    decisions = client.get(f"/api/v1/jobs/{job['id']}/decisions")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["decision"] == "interview"
    assert decisions.json() == [second.json()]


def test_resume_docx_upload_extracts_and_stores_candidate(monkeypatch):
    monkeypatch.setattr(
        resume_endpoint,
        "UPLOAD_DIR",
        make_upload_dir("resume_extract"),
    )
    client = TestClient(app)
    resume_bytes = build_docx_bytes(
        [
            "Upload Candidate",
            "upload-candidate@example.com",
            "+919876543210",
            "Python FastAPI Docker",
        ]
    )

    response = client.post(
        "/api/v1/resumes/extract",
        files={
            "file": (
                "resume.docx",
                resume_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()

    assert payload["created"] is True
    assert payload["candidate"]["full_name"] == "Upload Candidate"
    assert payload["candidate"]["email"] == "upload-candidate@example.com"
    assert payload["candidate"]["skills"] == ["Python", "FastAPI", "Docker"]


def test_resume_docx_duplicate_upload_returns_existing_candidate(
    monkeypatch,
):
    monkeypatch.setattr(
        resume_endpoint,
        "UPLOAD_DIR",
        make_upload_dir("resume_duplicate"),
    )
    client = TestClient(app)
    resume_bytes = build_docx_bytes(
        [
            "Duplicate Upload",
            "duplicate-upload@example.com",
            "Python FastAPI",
        ]
    )
    files = {
        "file": (
            "resume.docx",
            resume_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }

    first_response = client.post("/api/v1/resumes/extract", files=files)
    second_response = client.post("/api/v1/resumes/extract", files=files)

    assert first_response.status_code == 201
    assert second_response.status_code == 200
    assert second_response.json()["created"] is False
    assert second_response.json()["message"] == "Candidate already exists"


def test_resume_docx_upload_without_email_returns_bad_request(
    monkeypatch,
):
    monkeypatch.setattr(
        resume_endpoint,
        "UPLOAD_DIR",
        make_upload_dir("resume_no_email"),
    )
    client = TestClient(app)
    resume_bytes = build_docx_bytes(
        [
            "No Email Candidate",
            "Python FastAPI Docker",
        ]
    )

    response = client.post(
        "/api/v1/resumes/extract",
        files={
            "file": (
                "resume.docx",
                resume_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Could not extract candidate email"


def test_job_docx_upload_extracts_and_stores_job(monkeypatch):
    monkeypatch.setattr(
        job_endpoint,
        "UPLOAD_DIR",
        make_upload_dir("job_extract"),
    )
    client = TestClient(app)
    job_bytes = build_docx_bytes(
        [
            "Senior Backend Engineer",
            "Must have 4+ years experience with Python, FastAPI and Docker.",
            "Required knowledge of PostgreSQL.",
        ]
    )

    response = client.post(
        "/api/v1/jobs/extract",
        files={
            "file": (
                "backend-role.docx",
                job_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()

    assert payload["title"] == "backend-role"
    assert payload["min_experience"] == 4
    assert payload["skills"] == ["Python", "FastAPI", "Docker", "PostgreSQL"]
    assert payload["requirements"] == [
        "Must have 4+ years experience with Python, FastAPI and Docker.",
        "Required knowledge of PostgreSQL.",
    ]

from app.db.session import SessionLocal
from app.schemas.candidate import CandidateCreate
from app.schemas.job import JobCreate
from app.services.candidate_service import CandidateService
from app.services.job_service import JobService


DEMO_CANDIDATES = [
    CandidateCreate(
        full_name="Asha Backend",
        email="asha.backend@example.com",
        phone="+919876543210",
        years_experience=5,
        skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
        resume_path="uploads/resumes/demo-asha.pdf",
    ),
    CandidateCreate(
        full_name="Rohan Data",
        email="rohan.data@example.com",
        phone="+919876543211",
        years_experience=3,
        skills=["Python", "Pandas", "NumPy", "Scikit-learn"],
        resume_path="uploads/resumes/demo-rohan.pdf",
    ),
    CandidateCreate(
        full_name="Maya Frontend",
        email="maya.frontend@example.com",
        phone="+919876543212",
        years_experience=2,
        skills=["JavaScript", "Node.js", "Git"],
        resume_path="uploads/resumes/demo-maya.pdf",
    ),
]

DEMO_JOBS = [
    JobCreate(
        title="Senior Backend Engineer",
        description=(
            "Build APIs with Python, FastAPI, Docker and PostgreSQL. "
            "Must have 4+ years experience."
        ),
        min_experience=4,
        skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
        requirements=[
            "4+ years experience",
            "Python and FastAPI API development",
            "Docker experience",
            "PostgreSQL knowledge",
        ],
    ),
    JobCreate(
        title="Machine Learning Engineer",
        description=(
            "Develop ML pipelines with Python, Pandas, NumPy and Scikit-learn. "
            "Minimum 3 years experience."
        ),
        min_experience=3,
        skills=["Python", "Pandas", "NumPy", "Scikit-learn"],
        requirements=[
            "3+ years experience",
            "Python ML pipeline development",
            "Pandas and NumPy experience",
        ],
    ),
]


def seed_demo_data():
    db = SessionLocal()

    try:
        created_candidates = 0
        created_jobs = 0

        for candidate in DEMO_CANDIDATES:
            result = CandidateService.create(db, candidate)

            if result["created"]:
                created_candidates += 1

        existing_titles = {
            job.title
            for job in JobService.get_all(db)
        }

        for job in DEMO_JOBS:
            if job.title in existing_titles:
                continue

            JobService.create(db, job)
            created_jobs += 1

        return {
            "created_candidates": created_candidates,
            "created_jobs": created_jobs,
        }
    finally:
        db.close()


if __name__ == "__main__":
    result = seed_demo_data()
    print(
        "Seeded demo data: "
        f"{result['created_candidates']} candidates, "
        f"{result['created_jobs']} jobs."
    )

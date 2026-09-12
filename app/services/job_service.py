from app.services.extraction_service import (
    ExtractionService
)
from app.models.job import Job


class JobService:
    @staticmethod
    def create(db, data):
        job = Job(
            title=data.title,
            description=data.description,
            min_experience=data.min_experience,
            requirements=data.requirements,
            skills=data.skills
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        return job

    @staticmethod
    def create_from_text(db, title: str, text: str):
        skills = JobService.extract_jd_skills(text)
        min_experience = ExtractionService.extract_years_experience(text)
        requirements = ExtractionService.extract_requirements(text)

        job = Job(
            title=title,
            description=text,
            min_experience=min_experience,
            requirements=requirements,
            skills=skills
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        return job

    @staticmethod
    def get_all(db):
        return (
            db.query(Job)
            .order_by(Job.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_id(db, job_id: int):
        return (
            db.query(Job)
            .filter(Job.id == job_id)
            .first()
        )

    @staticmethod
    def update(db, job_id: int, data):
        job = JobService.get_by_id(
            db,
            job_id
        )

        if not job:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(job, field, value)

        db.commit()
        db.refresh(job)

        return job

    @staticmethod
    def delete(db, job_id: int):
        job = JobService.get_by_id(
            db,
            job_id
        )

        if not job:
            return False

        db.delete(job)
        db.commit()

        return True

    @staticmethod
    def extract_jd_skills(text: str):

        return ExtractionService.extract_skills(
            text
        )

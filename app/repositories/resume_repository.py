from sqlalchemy.orm import Session

from app.models.resume import Resume


class ResumeRepository:

    @staticmethod
    def create(
        db: Session,
        file_name: str,
        file_path: str,
        candidate_id=None
    ):

        resume = Resume(
            candidate_id=candidate_id,
            file_name=file_name,
            file_path=file_path
        )

        db.add(resume)
        db.commit()
        db.refresh(resume)

        return resume
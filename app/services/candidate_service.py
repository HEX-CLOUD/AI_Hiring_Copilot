from app.models.candidate import Candidate


class CandidateService:
    @staticmethod
    def _skills_to_string(skills):
        if not skills:
            return None

        if isinstance(skills, str):
            skills = skills.split(",")

        return ",".join(
            skill.strip()
            for skill in skills
            if skill and skill.strip()
        )

    @staticmethod
    def _serialize_candidate(candidate: Candidate):
        skills = []

        if candidate.skills:
            if isinstance(candidate.skills, str):
                raw_skills = candidate.skills.split(",")
            else:
                raw_skills = candidate.skills

            skills = [
                skill.strip()
                for skill in raw_skills
                if skill and skill.strip()
            ]

        return {
            "id": candidate.id,
            "full_name": candidate.full_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "years_experience": candidate.years_experience,
            "skills": skills,
            "resume_path": candidate.resume_path,
            "created_at": candidate.created_at,
            "updated_at": candidate.updated_at,
        }

    @staticmethod
    def create_candidate(
        db,
        name,
        email,
        phone,
        skills,
        resume_path
    ):
        if not name:
            name = "Unknown Candidate"

        if not email:
            return {
                "created": False,
                "status_code": 400,
                "message": "Could not extract candidate email",
                "candidate": None
            }

        existing_candidate = (
            db.query(Candidate)
            .filter(Candidate.email == email)
            .first()
        )

        if existing_candidate:
            return {
                "created": False,
                "status_code": 409,
                "message": "Candidate already exists",
                "candidate": existing_candidate
            }

        candidate = Candidate(
            full_name=name,
            email=email,
            phone=phone,
            skills=CandidateService._skills_to_string(skills),
            resume_path=resume_path
        )

        db.add(candidate)

        db.commit()

        db.refresh(candidate)

        return {
            "created": True,
            "status_code": 201,
            "message": "Candidate created successfully",
            "candidate": candidate
        }

    @staticmethod
    def create(db, data):
        result = CandidateService.create_candidate(
            db=db,
            name=data.full_name,
            email=data.email,
            phone=data.phone,
            skills=data.skills,
            resume_path=data.resume_path
        )

        if result["created"] and data.years_experience is not None:
            candidate = result["candidate"]
            candidate.years_experience = data.years_experience
            db.commit()
            db.refresh(candidate)

        return result

    @staticmethod
    def get_by_id(db, candidate_id: int):
        candidate = CandidateService.get_model_by_id(
            db,
            candidate_id
        )

        if not candidate:
            return None

        return CandidateService._serialize_candidate(candidate)

    @staticmethod
    def get_model_by_id(db, candidate_id: int):
        return (
            db.query(Candidate)
            .filter(Candidate.id == candidate_id)
            .first()
        )

    @staticmethod
    def get_all_models(db):
        return (
            db.query(Candidate)
            .order_by(Candidate.created_at.desc())
            .all()
        )

    @staticmethod
    def get_all_candidates(
        db,
        skills: str | None = None,
        min_experience: int | None = None,
        max_experience: int | None = None
    ):
        query = db.query(Candidate)

        if min_experience is not None:
            query = query.filter(
                Candidate.years_experience >= min_experience
            )

        if max_experience is not None:
            query = query.filter(
                Candidate.years_experience <= max_experience
            )

        candidates = query.order_by(
            Candidate.created_at.desc()
        ).all()

        if skills:
            required_skills = {
                skill.strip().lower()
                for skill in skills.split(",")
                if skill.strip()
            }

            candidates = [
                candidate
                for candidate in candidates
                if required_skills.issubset({
                    skill.lower()
                    for skill in CandidateService
                    ._serialize_candidate(candidate)["skills"]
                })
            ]

        return [
            CandidateService._serialize_candidate(candidate)
            for candidate in candidates
        ]

    @staticmethod
    def search(db, query_text: str):
        candidates = (
            db.query(Candidate)
            .filter(
                Candidate.full_name.ilike(f"%{query_text}%")
                | Candidate.email.ilike(f"%{query_text}%")
            )
            .order_by(Candidate.created_at.desc())
            .all()
        )

        return [
            CandidateService._serialize_candidate(candidate)
            for candidate in candidates
        ]

    @staticmethod
    def update(db, candidate_id: int, data):
        candidate = (
            db.query(Candidate)
            .filter(Candidate.id == candidate_id)
            .first()
        )

        if not candidate:
            return None

        if data.email and data.email != candidate.email:
            existing_candidate = (
                db.query(Candidate)
                .filter(Candidate.email == data.email)
                .first()
            )

            if existing_candidate:
                return {
                    "updated": False,
                    "status_code": 409,
                    "message": "Candidate email already exists",
                    "candidate": existing_candidate
                }

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "skills":
                value = CandidateService._skills_to_string(value)

            setattr(candidate, field, value)

        db.commit()
        db.refresh(candidate)

        return {
            "updated": True,
            "status_code": 200,
            "message": "Candidate updated successfully",
            "candidate": candidate
        }

    @staticmethod
    def delete(db, candidate_id: int):
        candidate = (
            db.query(Candidate)
            .filter(Candidate.id == candidate_id)
            .first()
        )

        if not candidate:
            return False

        db.delete(candidate)
        db.commit()

        return True

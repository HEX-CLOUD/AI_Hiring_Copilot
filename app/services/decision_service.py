from app.models.candidate_job_decision import CandidateJobDecision


class DecisionService:
    @staticmethod
    def _serialize(record: CandidateJobDecision):
        return {
            "candidate_id": record.candidate_id,
            "job_id": record.job_id,
            "decision": record.decision,
            "notes": record.notes,
            "updated_at": record.updated_at,
        }

    @staticmethod
    def get_for_job(db, job_id: int):
        records = (
            db.query(CandidateJobDecision)
            .filter(CandidateJobDecision.job_id == job_id)
            .order_by(CandidateJobDecision.updated_at.desc())
            .all()
        )
        return [DecisionService._serialize(record) for record in records]

    @staticmethod
    def upsert(db, candidate_id: int, job_id: int, decision: str, notes: str | None):
        record = (
            db.query(CandidateJobDecision)
            .filter(
                CandidateJobDecision.candidate_id == candidate_id,
                CandidateJobDecision.job_id == job_id,
            )
            .first()
        )

        if not record:
            record = CandidateJobDecision(
                candidate_id=candidate_id,
                job_id=job_id,
                decision=decision,
                notes=notes,
            )
            db.add(record)
        else:
            record.decision = decision
            record.notes = notes

        db.commit()
        db.refresh(record)
        return DecisionService._serialize(record)

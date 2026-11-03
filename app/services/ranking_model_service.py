"""Supervised ranking model trained only from recorded recruiter decisions.

The deterministic score remains the fallback until enough labelled feedback is
available. This prevents a demo dataset from being presented as recruiter
ground truth while still providing a real ML training and evaluation path.
"""

from datetime import UTC, datetime
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from app.core.config import settings
from app.models.candidate_job_decision import CandidateJobDecision
from app.services.candidate_service import CandidateService
from app.services.job_service import JobService
from app.services.matching_service import MatchingService


class RankingModelService:
    FEATURE_NAMES = [
        "skill_coverage",
        "experience_coverage",
        "project_count",
        "certification_count",
        "profile_completeness",
        "baseline_match_score",
    ]
    DECISION_LABELS = {"rejected": 0.0, "shortlisted": 0.7, "interview": 1.0}

    @staticmethod
    def _model_path() -> Path:
        return Path(settings.RANKING_MODEL_PATH)

    @staticmethod
    def _features(candidate, job) -> dict[str, float]:
        match = MatchingService.match_candidate_to_job(candidate, job)
        required_skills = len(job.skills or [])
        years = candidate.years_experience or 0
        required_years = job.min_experience or 0
        experience_coverage = 1.0 if required_years == 0 else min(years / required_years, 1.0)
        completed_sections = sum(bool(section) for section in [
            candidate.education,
            candidate.projects,
            candidate.certifications,
            candidate.work_history,
        ])
        return {
            "skill_coverage": round(len(match["matched_skills"]) / required_skills, 4) if required_skills else 0.0,
            "experience_coverage": round(experience_coverage, 4),
            "project_count": float(len(candidate.projects or [])),
            "certification_count": float(len(candidate.certifications or [])),
            "profile_completeness": round(completed_sections / 4, 4),
            "baseline_match_score": float(match["match_score"]),
        }

    @staticmethod
    def dataset_records(db) -> list[dict]:
        records = []
        decisions = db.query(CandidateJobDecision).all()
        for decision in decisions:
            if decision.decision not in RankingModelService.DECISION_LABELS:
                continue
            candidate = CandidateService.get_model_by_id(db, decision.candidate_id)
            job = JobService.get_by_id(db, decision.job_id)
            if not candidate or not job:
                continue
            records.append({
                "candidate_id": candidate.id,
                "job_id": job.id,
                "decision": decision.decision,
                "label": RankingModelService.DECISION_LABELS[decision.decision],
                "features": RankingModelService._features(candidate, job),
            })
        return records

    @staticmethod
    def status() -> dict:
        path = RankingModelService._model_path()
        base = {
            "trained": False,
            "training_samples": 0,
            "trained_at": None,
            "feature_names": RankingModelService.FEATURE_NAMES,
            "feature_importances": {},
            "metrics": {},
            "training_data_source": "recruiter decisions",
            "minimum_samples_required": settings.RANKING_MIN_TRAINING_SAMPLES,
        }
        if not path.exists():
            return base
        artifact = joblib.load(path)
        return {**base, **artifact["metadata"], "trained": True}

    @staticmethod
    def train(db) -> dict:
        records = RankingModelService.dataset_records(db)
        labels = [record["label"] for record in records]
        if len(records) < settings.RANKING_MIN_TRAINING_SAMPLES:
            raise ValueError(
                f"At least {settings.RANKING_MIN_TRAINING_SAMPLES} labelled recruiter decisions are required; found {len(records)}."
            )
        if len(set(labels)) < 2:
            raise ValueError("Training needs at least two different decision outcomes.")

        X = [[record["features"][name] for name in RankingModelService.FEATURE_NAMES] for record in records]
        model = RandomForestRegressor(n_estimators=200, random_state=42, min_samples_leaf=1)
        metrics = {"mae": None, "r2": None}
        if len(records) >= 8:
            X_train, X_test, y_train, y_test = train_test_split(
                X, labels, test_size=max(2, round(len(records) * 0.25)), random_state=42
            )
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)
            metrics = {
                "mae": round(float(mean_absolute_error(y_test, predictions)), 4),
                "r2": round(float(r2_score(y_test, predictions)), 4) if len(y_test) > 1 else None,
            }
        model.fit(X, labels)
        metadata = {
            "training_samples": len(records),
            "trained_at": datetime.now(UTC).isoformat(),
            "feature_names": RankingModelService.FEATURE_NAMES,
            "feature_importances": {
                name: round(float(importance), 4)
                for name, importance in zip(RankingModelService.FEATURE_NAMES, model.feature_importances_)
            },
            "metrics": metrics,
        }
        path = RankingModelService._model_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": model, "metadata": metadata}, path)
        return {**RankingModelService.status(), "message": "Ranking model trained from recruiter decisions."}

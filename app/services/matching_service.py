class MatchingService:
    SKILL_ALIASES = {
        "js": "javascript",
        "postgres": "postgresql",
        "postgresql": "postgresql",
        "py": "python",
        "scikit learn": "scikit-learn",
        "sklearn": "scikit-learn",
        "node": "node.js",
        "nodejs": "node.js",
    }

    @staticmethod
    def normalize_skill(skill: str):
        normalized = skill.strip().lower()
        normalized = normalized.replace("_", " ")

        return MatchingService.SKILL_ALIASES.get(
            normalized,
            normalized
        )

    @staticmethod
    def _candidate_skills(candidate):
        if not candidate.skills:
            return []

        if isinstance(candidate.skills, list):
            return candidate.skills

        return [
            skill.strip()
            for skill in candidate.skills.split(",")
            if skill.strip()
        ]

    @staticmethod
    def match_skills(
        candidate_skills: list[str],
        jd_skills: list[str],
        candidate_experience: int | None = None,
        required_experience: int | None = None
    ):

        candidate_set = set(
            MatchingService.normalize_skill(skill)
            for skill in candidate_skills
        )

        matched = []

        missing = []

        for skill in jd_skills:

            if MatchingService.normalize_skill(skill) in candidate_set:
                matched.append(skill)
            else:
                missing.append(skill)

        skill_score = 0

        if len(jd_skills) > 0:
            skill_score = (
                len(matched)
                / len(jd_skills)
            ) * 100

        experience_match = MatchingService.match_experience(
            candidate_experience,
            required_experience
        )

        if required_experience is None:
            score = skill_score
        else:
            experience_score = 100 if experience_match else 0
            score = (skill_score * 0.8) + (experience_score * 0.2)

        return {
            "match_score": round(score, 2),
            "matched_skills": matched,
            "missing_skills": missing,
            "candidate_experience": candidate_experience,
            "required_experience": required_experience,
            "experience_match": experience_match,
            "fit_explanation": MatchingService.build_fit_explanation(
                round(score, 2),
                matched,
                missing,
                experience_match,
                required_experience
            )
        }

    @staticmethod
    def match_experience(
        candidate_experience: int | None,
        required_experience: int | None
    ):
        if required_experience is None:
            return True

        if candidate_experience is None:
            return False

        return candidate_experience >= required_experience

    @staticmethod
    def build_fit_explanation(
        score: float,
        matched_skills: list[str],
        missing_skills: list[str],
        experience_match: bool = True,
        required_experience: int | None = None
    ):
        if score >= 80:
            fit_level = "strong"
        elif score >= 50:
            fit_level = "partial"
        else:
            fit_level = "low"

        matched_text = ", ".join(matched_skills) or "none"
        missing_text = ", ".join(missing_skills) or "none"
        experience_text = ""

        if required_experience is not None:
            if experience_match:
                experience_text = (
                    f" Meets the {required_experience}+ years requirement."
                )
            else:
                experience_text = (
                    f" Does not meet the {required_experience}+ years requirement."
                )

        return (
            f"This is a {fit_level} fit. "
            f"Matched skills: {matched_text}. "
            f"Missing skills: {missing_text}."
            f"{experience_text}"
        )

    @staticmethod
    def match_candidate_to_job(candidate, job):
        result = MatchingService.match_skills(
            MatchingService._candidate_skills(candidate),
            job.skills or [],
            candidate.years_experience,
            job.min_experience
        )

        return {
            "candidate_id": candidate.id,
            "candidate_name": candidate.full_name,
            "job_id": job.id,
            "job_title": job.title,
            **result
        }

    @staticmethod
    def rank_candidates_for_job(candidates, job):
        matches = [
            MatchingService.match_candidate_to_job(candidate, job)
            for candidate in candidates
        ]

        return sorted(
            matches,
            key=lambda match: match["match_score"],
            reverse=True
        )

    @staticmethod
    def rank_jobs_for_candidate(jobs, candidate):
        matches = [
            MatchingService.match_candidate_to_job(candidate, job)
            for job in jobs
        ]

        return sorted(
            matches,
            key=lambda match: match["match_score"],
            reverse=True
        )

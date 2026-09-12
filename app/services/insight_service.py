from app.services.matching_service import MatchingService


class InsightService:
    @staticmethod
    def build_candidate_summary(candidate, job, match):
        years = candidate.years_experience
        experience_text = (
            f"{years} years of experience"
            if years is not None
            else "experience not specified"
        )

        return (
            f"{candidate.full_name} is being evaluated for "
            f"{job.title or 'this role'} with {experience_text}. "
            f"The candidate matched {len(match['matched_skills'])} of "
            f"{len(job.skills or [])} required skills."
        )

    @staticmethod
    def build_strengths(match):
        strengths = []

        if match["matched_skills"]:
            strengths.append(
                "Matches required skills: "
                + ", ".join(match["matched_skills"])
            )

        if match["experience_match"]:
            strengths.append("Meets the minimum experience requirement")

        if match["match_score"] >= 80:
            strengths.append("Overall profile is a strong fit for the role")

        return strengths or ["No clear strengths found from the available data"]

    @staticmethod
    def build_weaknesses(match):
        weaknesses = []

        if match["missing_skills"]:
            weaknesses.append(
                "Missing required skills: "
                + ", ".join(match["missing_skills"])
            )

        if not match["experience_match"]:
            weaknesses.append("Does not meet the minimum experience requirement")

        return weaknesses or ["No major gaps found from the available data"]

    @staticmethod
    def build_recommendation(match):
        score = match["match_score"]

        if score >= 85:
            return (
                "Strong recommend",
                "High match score with strong coverage of role requirements.",
            )

        if score >= 65:
            return (
                "Recommend",
                "Good fit with some gaps that can be explored in interviews.",
            )

        if score >= 45:
            return (
                "Consider with caution",
                "Partial fit; review the missing skills and experience gap.",
            )

        return (
            "Not recommended",
            "Low fit against the current role requirements.",
        )

    @staticmethod
    def generate_candidate_job_insight(candidate, job):
        match = MatchingService.match_candidate_to_job(candidate, job)
        recommendation, reason = InsightService.build_recommendation(match)

        return {
            **match,
            "candidate_summary": InsightService.build_candidate_summary(
                candidate,
                job,
                match,
            ),
            "strengths": InsightService.build_strengths(match),
            "weaknesses": InsightService.build_weaknesses(match),
            "hiring_recommendation": recommendation,
            "recommendation_reason": reason,
        }

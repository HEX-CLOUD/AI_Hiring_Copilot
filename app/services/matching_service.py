class MatchingService:

    @staticmethod
    def match_skills(
        candidate_skills: list[str],
        jd_skills: list[str]
    ):

        candidate_set = set(
            skill.lower()
            for skill in candidate_skills
        )

        jd_set = set(
            skill.lower()
            for skill in jd_skills
        )

        matched = []

        missing = []

        for skill in jd_skills:

            if skill.lower() in candidate_set:
                matched.append(skill)
            else:
                missing.append(skill)

        score = 0

        if len(jd_skills) > 0:
            score = (
                len(matched)
                / len(jd_skills)
            ) * 100

        return {
            "match_score": round(score, 2),
            "matched_skills": matched,
            "missing_skills": missing
        }
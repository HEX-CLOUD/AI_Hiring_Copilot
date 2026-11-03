import re

from app.services.candidate_service import CandidateService
from app.services.matching_service import MatchingService


class SearchService:
    STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "for",
        "in",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
        "years",
        "year",
        "yr",
        "yrs",
        "more",
        "minimum",
        "minimums",
        "at",
        "least",
        "over",
        "above",
        "plus",
        "experience",
        "candidate",
        "engineer",
        "developer",
    }

    @staticmethod
    def tokenize(text: str):
        tokens = re.findall(r"[A-Za-z0-9+#.]+", text.lower())

        return {
            MatchingService.normalize_skill(token)
            for token in tokens
            if token not in SearchService.STOP_WORDS
        }

    @staticmethod
    def candidate_document(candidate):
        serialized = CandidateService._serialize_candidate(candidate)

        return " ".join(
            [
                serialized["full_name"] or "",
                serialized["email"] or "",
                str(serialized["years_experience"] or ""),
                " ".join(serialized["skills"]),
                " ".join(serialized["education"]),
                " ".join(serialized["projects"]),
                " ".join(serialized["certifications"]),
                " ".join(serialized["work_history"]),
                serialized["source_text"] or "",
            ]
        )

    @staticmethod
    def score_candidate(query: str, candidate):
        query_tokens = SearchService.tokenize(query)

        if not query_tokens:
            return {
                "score": 0,
                "matched_terms": [],
            }

        candidate_tokens = SearchService.tokenize(
            SearchService.candidate_document(candidate)
        )
        matched_terms = sorted(query_tokens.intersection(candidate_tokens))
        score = (len(matched_terms) / len(query_tokens)) * 100

        return {
            "score": round(score, 2),
            "matched_terms": matched_terms,
        }

    @staticmethod
    def search_candidates(db, query: str, limit: int = 10):
        candidates = CandidateService.get_all_models(db)
        results = []

        for candidate in candidates:
            score_result = SearchService.score_candidate(query, candidate)

            if score_result["score"] <= 0:
                continue

            serialized = CandidateService._serialize_candidate(candidate)
            matched_terms = score_result["matched_terms"]
            matched_text = ", ".join(matched_terms) or "none"

            results.append(
                {
                    **serialized,
                    "relevance_score": score_result["score"],
                    "matched_terms": matched_terms,
                    "search_explanation": (
                        f"Matched query terms: {matched_text}."
                    ),
                }
            )

        return sorted(
            results,
            key=lambda result: result["relevance_score"],
            reverse=True,
        )[:limit]

    @staticmethod
    def search_candidates_with_filters(db, query: str, filters: dict, limit: int = 10):
        """Apply validated SQL constraints before any relevance ranking."""
        if filters.get("has_constraints"):
            selected, _ = SearchService.filter_candidate_models(db, filters)
            return SearchService.rank_filtered_candidates(query, selected, limit)
        return SearchService.search_candidates(db, query, limit)

    @staticmethod
    def filter_candidate_models(db, filters: dict):
        """Compile a validated filter plan into parameterized SQLAlchemy SQL.

        The LLM never supplies SQL. It only proposes a small typed plan, and
        this method is the sole compiler from that plan to database predicates.
        """
        from sqlalchemy import and_, case, func, literal, not_, or_
        from app.models.candidate import Candidate

        query = db.query(Candidate)
        clauses = []
        min_years = filters.get("min_experience")
        max_years = filters.get("max_experience")
        if min_years is not None:
            clauses.append(Candidate.years_experience >= min_years)
        if max_years is not None:
            clauses.append(Candidate.years_experience <= max_years)

        # Candidate skills are stored as normalized comma-separated tokens.
        # Wrapping both sides with commas prevents "Java" matching "JavaScript".
        skill_text = literal(",") + func.lower(func.coalesce(Candidate.skills, "")) + literal(",")

        def escape_like(value: str) -> str:
            return value.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

        def has_skill(value: str):
            return skill_text.like(f"%,{escape_like(value)},%", escape="\\")

        required = [has_skill(skill) for skill in filters.get("required_skills", [])]
        alternatives = [has_skill(skill) for skill in filters.get("any_skills", [])]
        exclusive = [has_skill(skill) for skill in filters.get("exclusive_skills", [])]
        excluded = [has_skill(skill) for skill in filters.get("excluded_skills", [])]
        required_terms = filters.get("required_terms", [])
        if required:
            clauses.append(and_(*required))
        if alternatives:
            clauses.append(or_(*alternatives))
        if exclusive:
            # XOR means exactly one named skill. A profile containing both
            # Python and Java therefore fails this predicate.
            clauses.append(sum((case((predicate, 1), else_=0) for predicate in exclusive), literal(0)) == 1)
        if excluded:
            clauses.extend(not_(predicate) for predicate in excluded)
        if required_terms:
            profile_text = func.lower(func.coalesce(Candidate.source_text, ""))
            clauses.extend(
                profile_text.like(f"%{escape_like(term)}%", escape="\\")
                for term in required_terms
            )

        if clauses:
            query = query.filter(and_(*clauses))
        query = query.order_by(Candidate.years_experience.desc(), Candidate.id.asc())
        compiled = query.statement.compile(
            dialect=db.get_bind().dialect,
            compile_kwargs={"literal_binds": True},
        )
        sql_preview = " ".join(str(compiled).split())
        return query.all(), sql_preview

    @staticmethod
    def rank_filtered_candidates(query: str, candidates: list, limit: int):
        results = []
        for candidate in candidates:
            lexical = SearchService.score_candidate(query, candidate)
            serialized = CandidateService._serialize_candidate(candidate)
            results.append({
                **serialized,
                "relevance_score": lexical["score"],
                "matched_terms": lexical["matched_terms"],
                "search_explanation": "Matched the explicit experience/skill filters; ranked by query evidence.",
            })
        return sorted(results, key=lambda item: item["relevance_score"], reverse=True)[:limit]

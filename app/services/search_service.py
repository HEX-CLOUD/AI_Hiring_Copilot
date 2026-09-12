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

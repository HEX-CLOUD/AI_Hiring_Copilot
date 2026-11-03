"""Convert recruiter language into a validated candidate filter plan.

The local LLM may propose values, but it never emits executable SQL. The
validated plan is compiled to SQLAlchemy by SearchService.
"""

import json
import re
from functools import lru_cache
from urllib import error, request

from app.core.config import settings
from app.services.candidate_service import CandidateService
from app.services.matching_service import MatchingService


class QueryPlanningService:
    OPERATORS = {"AND", "OR", "XOR"}

    @staticmethod
    def _skill_vocabulary(db) -> list[str]:
        skills = {
            skill
            for candidate in CandidateService.get_all_models(db)
            for skill in CandidateService._serialize_candidate(candidate)["skills"]
        }
        return sorted(skills, key=str.lower)

    @staticmethod
    def interpret(db, query: str) -> dict:
        vocabulary = QueryPlanningService._skill_vocabulary(db)
        proposed = QueryPlanningService._llm_plan(query, tuple(vocabulary))
        if proposed is None:
            # Do not silently invent structured constraints if the configured
            # local LLM is unavailable. Semantic retrieval remains available.
            proposed = {
                "min_experience": None,
                "max_experience": None,
                "skills": [],
                "required_terms": [],
                "candidate_search": True,
                "skill_operator": "AND",
                "excluded_skills": [],
                "semantic_query": query,
            }
            parser = "local-llm-unavailable-semantic-only"
        else:
            parser = f"local-llm-query-planner:{settings.OLLAMA_MODEL}"
        return QueryPlanningService._validate(proposed, vocabulary, parser, query)

    @staticmethod
    @lru_cache(maxsize=256)
    def _llm_plan(query: str, vocabulary: tuple[str, ...]) -> dict | None:
        if not settings.OLLAMA_BASE_URL:
            return None
        prompt = (
            "Convert the recruiter query into JSON only. Allowed fields: "
            "min_experience (integer or null), max_experience (integer or null), "
            "skills (array), skill_operator (AND, OR, or XOR), excluded_skills (array), "
            "required_terms (array of role/domain words explicitly present in the query), candidate_search (boolean), semantic_query (string). "
            "XOR means exactly one listed skill and excludes candidates with both. "
            "Use AND when all named skills are required. Add a filter only when it is explicitly stated in the recruiter query. "
            "For example, 'backend and python' should use skills=['Python'] and required_terms=['backend']. "
            "For a broad semantic query with no explicit constraints, return null experience values and empty skills. "
            "Set candidate_search=false for general-knowledge questions unrelated to finding or evaluating people, resumes, roles, skills, projects, education, or experience. "
            "semantic_query must be a short embedding-search reformulation that preserves the recruiter intent and may add closely related professional concepts for a named domain. "
            "For example, for 'microservices experience', semantic_query can be 'microservices backend distributed services APIs'. "
            "Do not add hard requirements, candidate names, or unrelated technologies. "
            "Do not infer years of experience, skills, or exclusions from the candidate vocabulary. "
            f"Known skills: {', '.join(vocabulary)}\nRecruiter query: {query}"
        )
        try:
            body = json.dumps({
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0, "num_predict": 220},
            }).encode()
            response = request.urlopen(
                request.Request(
                    f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                    data=body,
                    headers={"Content-Type": "application/json"},
                ),
                timeout=settings.OLLAMA_TIMEOUT_SECONDS,
            )
            content = json.loads(response.read().decode()).get("response", "")
            return json.loads(content)
        except (error.URLError, TimeoutError, json.JSONDecodeError, OSError, TypeError):
            return None

    @staticmethod
    def _validate(plan: dict, vocabulary: list[str], parser: str, query: str) -> dict:
        vocabulary_map = {
            MatchingService.normalize_skill(skill): skill
            for skill in vocabulary
        }

        def is_explicitly_mentioned(skill: str) -> bool:
            """Prevent an LLM from inventing hard filters for broad queries.

            The LLM decides the operator and intent, while a structured skill
            filter is allowed only when the recruiter actually named that skill
            (or a supported alias) in their query. Broad queries stay semantic.
            """
            normalized = MatchingService.normalize_skill(skill)
            aliases = [normalized] + [
                alias
                for alias, canonical in MatchingService.SKILL_ALIASES.items()
                if canonical == normalized
            ]
            return any(
                re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", query.lower())
                for alias in aliases
            )

        requested = plan.get("skills") if isinstance(plan.get("skills"), list) else []
        skills = []
        for skill in requested:
            normalized = MatchingService.normalize_skill(str(skill))
            canonical = vocabulary_map.get(normalized)
            if canonical and is_explicitly_mentioned(canonical) and canonical.lower() not in {item.lower() for item in skills}:
                skills.append(canonical)
        excluded_requested = plan.get("excluded_skills") if isinstance(plan.get("excluded_skills"), list) else []
        excluded = [
            canonical
            for skill in excluded_requested
            if (canonical := vocabulary_map.get(MatchingService.normalize_skill(str(skill))))
            and is_explicitly_mentioned(canonical)
        ]
        requested_terms = plan.get("required_terms") if isinstance(plan.get("required_terms"), list) else []
        semantic_terms = []
        for term in requested_terms:
            normalized = re.sub(r"\s+", " ", str(term).strip().lower())
            if (
                len(normalized) >= 3
                and re.fullmatch(r"[a-z0-9+#. ]+", normalized)
                and re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", query.lower())
                and normalized not in semantic_terms
            ):
                semantic_terms.append(normalized)
        operator = str(plan.get("skill_operator", "AND")).upper()
        if operator not in QueryPlanningService.OPERATORS:
            operator = "AND"

        def valid_year(value):
            return value if isinstance(value, int) and 0 <= value <= 60 else None

        min_experience = valid_year(plan.get("min_experience"))
        max_experience = valid_year(plan.get("max_experience"))
        semantic_query = str(plan.get("semantic_query") or "").strip()
        if not semantic_query or len(semantic_query) > 500:
            semantic_query = query
        return {
            "min_experience": min_experience,
            "max_experience": max_experience,
            "required_skills": skills if operator == "AND" else [],
            "any_skills": skills if operator == "OR" else [],
            "exclusive_skills": skills if operator == "XOR" else [],
            "excluded_skills": excluded,
            # Role and domain language is deliberately a *semantic focus*, not
            # a SQL predicate. Requiring the exact word "microservices" would
            # incorrectly exclude profiles describing the same work as APIs,
            # backend services, distributed systems, or event-driven systems.
            # Years, named skills and exclusions remain exact constraints.
            "required_terms": [],
            "semantic_terms": semantic_terms,
            "candidate_search": bool(plan.get("candidate_search", True)),
            "skill_operator": operator,
            "semantic_query": semantic_query,
            "has_constraints": min_experience is not None or max_experience is not None or bool(skills) or bool(excluded),
            "parser": parser,
        }

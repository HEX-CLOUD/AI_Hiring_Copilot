import json
from time import perf_counter
from urllib import error, request

from app.core.config import settings
from app.services.vector_search_service import VectorSearchService
from app.services.query_planning_service import QueryPlanningService


class AIRetrievalService:

    @staticmethod
    def build_recruiter_brief(db, query: str, limit: int, generate: bool = False):
        started_at = perf_counter()
        filters = QueryPlanningService.interpret(db, query)
        ranking_query = filters.get("semantic_query") or query
        sources, retrieval = VectorSearchService.search_candidates(db, ranking_query, limit, filters)

        if not sources:
            answer = (
                "No candidate satisfied every interpreted constraint. "
                "Review the experience, skill operator, and exclusions below or broaden the query."
                if filters.get("has_constraints")
                else "No grounded candidate evidence matched this query. Try naming skills, domains, projects, or experience terms."
            )
        else:
            leaders = ", ".join(
                f"{source['full_name']} ({source['relevance_score']:.0f}%)"
                for source in sources[:3]
            )
            if generate:
                answer, generation_mode, generated_with_model = (
                    AIRetrievalService._generate_answer(query, sources, leaders)
                )
            else:
                answer = (
                    f"Semantic retrieval found {len(sources)} relevant candidate "
                    f"profile{'s' if len(sources) != 1 else ''} for '{query}'. "
                    f"Top evidence: {leaders}. Generate a local brief when you need a written synthesis."
                )
                generation_mode = "retrieval-only"
                generated_with_model = None

        if not sources:
            generation_mode = "retrieval-only"
            generated_with_model = None

        return {
            "answer": answer,
            "retrieval_method": retrieval["method"],
            "grounding_note": (
                "Results are grounded only in stored candidate profiles. "
                + ("Vector embeddings are active. " if retrieval["semantic"] else retrieval["fallback_reason"] + " ")
                + AIRetrievalService._generation_note(generation_mode)
            ),
            "semantic_retrieval_active": retrieval["semantic"],
            "generation_mode": generation_mode,
            "generated_with_model": generated_with_model,
            "source_candidate_ids": [source["id"] for source in sources],
            "retrieval_latency_ms": round((perf_counter() - started_at) * 1000, 1),
            "index_sync": retrieval["index_sync"],
            "interpreted_filters": filters,
            "sources": sources,
        }

    @staticmethod
    def _generation_note(generation_mode: str) -> str:
        if generation_mode == "ollama-rag":
            return "The brief was generated locally by Ollama using only the retrieved evidence."
        if generation_mode == "retrieval-only":
            return "This is a fast retrieval-only result; no generative model was used."
        return "The brief uses a deterministic grounded summary and does not use an external LLM."

    @staticmethod
    def _generate_answer(query: str, sources: list[dict], leaders: str) -> tuple[str, str, str | None]:
        fallback = (
            f"Grounded AI retrieval found {len(sources)} relevant candidate "
            f"profile{'s' if len(sources) != 1 else ''} for '{query}'. "
            f"Top evidence: {leaders}. Review the retrieved evidence before making a decision."
        )
        if not settings.OLLAMA_BASE_URL:
            return fallback, "deterministic-grounded-summary", None
        evidence = "\n".join(
            f"- Candidate: {item['full_name']}\n"
            f"  Years of experience: {item['years_experience'] if item['years_experience'] is not None else 'not listed'}\n"
            f"  Listed skills: {', '.join(item['skills']) or 'not listed'}\n"
            f"  Listed projects: {'; '.join(item['projects']) or 'not listed'}\n"
            f"  Listed work history: {'; '.join(item['work_history']) or 'not listed'}"
            for item in sources[:5]
        )
        prompt = (
            "You are TalentIQ, a recruiting decision-support assistant. "
            "Write a concise evidence brief in 2-4 bullets using ONLY the supplied profile facts. "
            "Each bullet must name the candidate and state only listed skills, listed projects, listed work history, or stated years. "
            "Do not invent a job description, project, requirement, qualification, or outcome. "
            "Do not claim a candidate is suitable, aligned, eligible, selected, or recommended. "
            "Do not mention semantic scores, SQL, models, or the retrieval pipeline. "
            "Do not infer protected traits or make a final hiring decision. State when evidence is not listed.\n"
            f"Query: {query}\nEvidence:\n{evidence}"
        )
        try:
            body = json.dumps({
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": settings.OLLAMA_MAX_TOKENS},
            }).encode()
            response = request.urlopen(
                request.Request(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate", data=body, headers={"Content-Type": "application/json"}),
                timeout=settings.OLLAMA_TIMEOUT_SECONDS,
            )
            generated = json.loads(response.read().decode()).get("response", "").strip()
            if generated:
                return generated, "ollama-rag", settings.OLLAMA_MODEL
            return fallback, "deterministic-grounded-summary", None
        except (error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return fallback, "deterministic-grounded-summary", None

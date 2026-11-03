"""Local embedding and vector retrieval for candidate profiles.

The service stays deliberately independent of the request lifecycle: ChromaDB
persists vectors, while PostgreSQL remains the source of truth for profiles.
If the embedding model is not installed/downloaded yet, callers receive a
safe lexical fallback instead of an opaque API failure.
"""

import os
import json
import hashlib
from functools import lru_cache
from urllib import error, request

from app.core.config import settings
from app.services.candidate_service import CandidateService
from app.services.search_service import SearchService


class VectorSearchService:
    COLLECTION_NAME = "candidate_profiles"
    _load_error: str | None = None

    @staticmethod
    @lru_cache(maxsize=1)
    def _model():
        # Avoid a model download as part of an automated test suite. The normal
        # API process downloads all-MiniLM-L6-v2 on its first semantic query.
        if os.environ.get("PYTEST_CURRENT_TEST"):
            raise RuntimeError("Embedding model loading is disabled during tests")

        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(
            settings.EMBEDDING_MODEL_NAME,
            local_files_only=settings.EMBEDDING_LOCAL_ONLY,
        )

    @staticmethod
    @lru_cache(maxsize=1)
    def _collection():
        import chromadb

        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        return client.get_or_create_collection(
            name=VectorSearchService.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def candidate_document(candidate) -> str:
        return SearchService.candidate_document(candidate)

    @staticmethod
    def _embedding(texts: list[str]):
        return VectorSearchService._model().encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

    @staticmethod
    def is_result_relevant(score: float, matched_terms: list[str]) -> bool:
        """Do not present a nearest neighbour as a match without evidence."""
        return (
            score >= settings.SEMANTIC_MIN_RELEVANCE_SCORE
            or bool(matched_terms)
        )

    @staticmethod
    def _document_hash(document: str) -> str:
        return hashlib.sha256(document.encode("utf-8")).hexdigest()

    @staticmethod
    def sync_candidates(db, force: bool = False) -> dict:
        candidates = CandidateService.get_all_models(db)
        collection = VectorSearchService._collection()
        existing = collection.get(include=["metadatas"])
        existing_metadata = {
            item_id: metadata or {}
            for item_id, metadata in zip(
                existing.get("ids") or [],
                existing.get("metadatas") or [],
            )
        }
        current_ids = {str(candidate.id) for candidate in candidates}
        stale_ids = [item_id for item_id in existing_metadata if item_id not in current_ids]
        if stale_ids:
            collection.delete(ids=stale_ids)

        changed = []
        for candidate in candidates:
            document = VectorSearchService.candidate_document(candidate)
            document_hash = VectorSearchService._document_hash(document)
            current_metadata = existing_metadata.get(str(candidate.id), {})
            if force or current_metadata.get("document_hash") != document_hash:
                changed.append((candidate, document, document_hash))

        if changed:
            collection.upsert(
                ids=[str(candidate.id) for candidate, _, _ in changed],
                documents=[document for _, document, _ in changed],
                embeddings=VectorSearchService._embedding(
                    [document for _, document, _ in changed]
                ),
                metadatas=[
                    {
                        "candidate_id": candidate.id,
                        "full_name": candidate.full_name,
                        "document_hash": document_hash,
                    }
                    for candidate, _, document_hash in changed
                ],
            )
        return {
            "indexed": len(changed),
            "unchanged": len(candidates) - len(changed),
            "removed": len(stale_ids),
            "total": len(candidates),
            "model": settings.EMBEDDING_MODEL_NAME,
        }

    @staticmethod
    def search_candidates(db, query: str, limit: int = 10, filters: dict | None = None):
        """Return results plus method metadata, degrading safely if offline."""
        try:
            index_sync = VectorSearchService.sync_candidates(db)
            collection = VectorSearchService._collection()
            candidate_count = len(CandidateService.get_all_models(db))
            result = collection.query(
                query_embeddings=VectorSearchService._embedding([query]),
                # Query the available pool before filtering. Otherwise, a low
                # relevance result can crowd out a genuinely relevant one.
                n_results=max(candidate_count, limit),
                include=["distances", "metadatas"],
            )
            distances = (result.get("distances") or [[]])[0]
            metadatas = (result.get("metadatas") or [[]])[0]
            candidate_ids = [metadata["candidate_id"] for metadata in metadatas]
            has_constraints = bool(filters and filters.get("has_constraints"))
            if has_constraints:
                filtered, sql_preview = SearchService.filter_candidate_models(db, filters)
                filters["sql_preview"] = sql_preview
                allowed_ids = {item.id for item in filtered}
            else:
                allowed_ids = {item.id for item in CandidateService.get_all_models(db)}
            candidates = {item.id: item for item in CandidateService.get_all_models(db) if item.id in candidate_ids and item.id in allowed_ids}
            results = []
            for candidate_id, distance in zip(candidate_ids, distances):
                candidate = candidates.get(candidate_id)
                if not candidate:
                    continue
                serialized = CandidateService._serialize_candidate(candidate)
                lexical = SearchService.score_candidate(query, candidate)
                score = max(0, min(100, round((1 - float(distance)) * 100, 2)))
                if not has_constraints and not VectorSearchService.is_result_relevant(
                    score,
                    lexical["matched_terms"],
                ):
                    continue
                results.append({
                    **serialized,
                    "relevance_score": score,
                    "matched_terms": lexical["matched_terms"],
                    "search_explanation": (
                        ("Satisfied every exact SQL constraint; " if has_constraints else "")
                        + f"semantic similarity: {score:.0f}% using {settings.EMBEDDING_MODEL_NAME}."
                    ),
                })
            results.sort(key=lambda item: item["relevance_score"], reverse=True)
            VectorSearchService._load_error = None
            return results[:limit], {
                "method": (
                    f"Validated SQL constraints + vector reranking ({settings.EMBEDDING_MODEL_NAME})"
                    if has_constraints
                    else f"Vector semantic search ({settings.EMBEDDING_MODEL_NAME} + ChromaDB cosine similarity)"
                ),
                "semantic": True,
                "fallback_reason": None,
                "index_sync": {
                    key: value
                    for key, value in index_sync.items()
                    if key != "model"
                },
            }
        except Exception as error:  # The app stays usable before a first model download.
            VectorSearchService._load_error = str(error)
            if filters and filters.get("has_constraints"):
                filtered, sql_preview = SearchService.filter_candidate_models(db, filters)
                filters["sql_preview"] = sql_preview
                fallback = SearchService.search_candidates_with_filters(db, query, filters, limit)
            else:
                fallback = SearchService.search_candidates(db, query, limit)
            return fallback, {
                "method": "Lexical retrieval fallback (embedding model unavailable)",
                "semantic": False,
                "fallback_reason": "Download/start the local embedding model to enable vector semantic retrieval.",
                "index_sync": {"indexed": 0, "unchanged": 0, "removed": 0, "total": 0},
            }

    @staticmethod
    def status() -> dict:
        ollama_reachable, ollama_model_available = VectorSearchService._ollama_status()
        return {
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "vector_store": "ChromaDB",
            "last_error": VectorSearchService._load_error,
            "ollama_configured": bool(settings.OLLAMA_BASE_URL),
            "ollama_model": settings.OLLAMA_MODEL,
            "ollama_reachable": ollama_reachable,
            "ollama_model_available": ollama_model_available,
        }

    @staticmethod
    def _ollama_status() -> tuple[bool, bool]:
        if not settings.OLLAMA_BASE_URL:
            return False, False
        try:
            response = request.urlopen(
                f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags",
                timeout=2,
            )
            models = json.loads(response.read().decode()).get("models", [])
            names = {model.get("name") for model in models}
            return True, settings.OLLAMA_MODEL in names
        except (error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return False, False

    @staticmethod
    def runtime_check() -> dict:
        status = VectorSearchService.status()
        # Model loading stays lazy, so this does not force a model download merely
        # because a recruiter opens the dashboard.
        return {
            **status,
            "semantic_retrieval_ready": status["last_error"] is None,
            "generation_ready": status["ollama_reachable"] and status["ollama_model_available"],
        }

    @staticmethod
    def warmup() -> None:
        """Load the local model off the request path when AI Intelligence opens."""
        try:
            VectorSearchService._model()
            VectorSearchService._collection()
            VectorSearchService._load_error = None
        except Exception as error:
            VectorSearchService._load_error = str(error)

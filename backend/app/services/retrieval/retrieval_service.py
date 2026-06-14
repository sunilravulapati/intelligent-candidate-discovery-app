import os
import logging
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from app.core.config import settings
from app.ml.faiss_index import CandidateFaissIndex
from app.ml.embedding_model import CandidateEmbeddingModel, EMBEDDING_DIM
from app.services.ingestion.ingestion_service import IngestionService

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Manages candidate profile retrieval using FAISS semantic vector search.

    Startup sequence:
      1. Load all clean candidates into memory (candidates_cache).
      2. Attempt to load the pre-built FAISS index from disk.
         - If found  → semantic mode (FAISS cosine search).
         - If missing → keyword fallback mode (full-scan in jobs.py).

    Query sequence (semantic mode):
      embed(job_query) → FAISS top-500 → lookup profiles from cache
    """

    # Relative path from the backend root, resolved at runtime
    DEFAULT_INDEX_PATH = "../data/embeddings/faiss_candidates.index"

    def __init__(self, index_path: Optional[str] = None):
        resolved = settings.get_absolute_path(
            index_path or self.DEFAULT_INDEX_PATH
        )
        self._index_path: str = resolved
        self._faiss: CandidateFaissIndex = CandidateFaissIndex(dimension=EMBEDDING_DIM)
        self._embedding_model: Optional[CandidateEmbeddingModel] = None
        self._semantic_ready: bool = False
        self._cache_loaded: bool = False

        # In-memory candidate profile store: candidate_id → profile dict
        self.candidates_cache: Dict[str, Dict[str, Any]] = {}

    # ── Public status helpers ─────────────────────────────────────

    def is_semantic_ready(self) -> bool:
        """Returns True when FAISS index is loaded and has vectors."""
        return self._semantic_ready and self._faiss.is_loaded()

    def is_cache_loaded(self) -> bool:
        """Returns True when the candidate profile cache is populated."""
        return self._cache_loaded

    # ── Startup loading ───────────────────────────────────────────

    def load_index_and_cache(self, ingestion_service: IngestionService) -> None:
        """
        Loads candidates into the in-memory cache and attempts to load the FAISS index.
        Idempotent — safe to call multiple times.
        """
        self._load_candidate_cache(ingestion_service)
        self._load_faiss_index()

    def _load_candidate_cache(self, ingestion_service: IngestionService) -> None:
        if self._cache_loaded:
            return
        logger.info("Loading all clean candidate profiles into memory cache...")
        candidates = ingestion_service.load_all_candidates(
            limit=-1,
            validate=True,
            preprocess=True,
            exclude_honeypots=True,
            as_dict=True,
        )
        self.candidates_cache = {c["candidate_id"]: c for c in candidates}
        self._cache_loaded = True
        logger.info(f"  Cache ready: {len(self.candidates_cache):,} candidates loaded.")

    def _load_faiss_index(self) -> None:
        if self._semantic_ready:
            return
        if not os.path.exists(self._index_path):
            logger.warning(
                f"FAISS index not found at '{self._index_path}'. "
                "Running in keyword-fallback mode. "
                "Build the index with: python scripts/build_semantic_index.py"
            )
            return
        try:
            logger.info(f"Loading FAISS index from '{self._index_path}'...")
            self._faiss.load(self._index_path)
            self._embedding_model = CandidateEmbeddingModel()
            self._semantic_ready = True
            logger.info(
                f"  FAISS index ready: {self._faiss.ntotal:,} vectors, "
                f"dim={EMBEDDING_DIM}. Semantic retrieval enabled."
            )
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}. Falling back to keyword mode.")
            self._semantic_ready = False

    # ── Retrieval ─────────────────────────────────────────────────

    def retrieve_candidates(
        self,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        top_k: int = 500,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieves the top_k most semantically similar candidates for a job query.

        In semantic mode: embeds the job query → FAISS cosine search → profile lookup.
        In keyword mode: returns all cached candidates with score=0.0 (Jaccard in jobs.py).

        Args:
            job_title: Job title string.
            job_description: Full job description.
            required_skills: List of required skill strings.
            top_k: Number of candidates to retrieve (pre-filter pool for hybrid ranking).

        Returns:
            List of (candidate_dict, semantic_similarity_score) tuples.
            Score is in [0, 1] in semantic mode, 0.0 in keyword mode.
        """
        if not self._semantic_ready:
            # Keyword fallback — return all candidates, scores set to 0.0
            return [(c, 0.0) for c in self.candidates_cache.values()]

        # Embed the job query
        assert self._embedding_model is not None
        query_text = self._embedding_model.build_job_query_string(
            job_title, job_description, required_skills
        )
        query_vec = self._embedding_model.encode(
            query_text,
            batch_size=1,
            normalize=True,  # Normalise for cosine similarity
        )

        # FAISS search
        hits = self._faiss.search(query_vec, top_k=top_k)

        # Map back to candidate profiles
        results: List[Tuple[Dict[str, Any], float]] = []
        for cand_id, score in hits:
            profile = self.candidates_cache.get(cand_id)
            if profile is not None:
                results.append((profile, float(score)))

        return results

import os
import logging
import time
import threading
import hashlib
import re
from collections import OrderedDict
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

    def __init__(self, index_path: Optional[str] = None):
        resolved = settings.get_absolute_path(
            index_path or settings.FAISS_INDEX_PATH
        )
        self._index_path: str = resolved
        self._faiss: CandidateFaissIndex = CandidateFaissIndex(dimension=EMBEDDING_DIM)
        self._embedding_model: Optional[CandidateEmbeddingModel] = None
        self._semantic_ready: bool = False
        self._cache_loaded: bool = False
        self._load_lock = threading.Lock()
        self._embedding_cache_lock = threading.Lock()
        self._embedding_cache: "OrderedDict[str, np.ndarray]" = OrderedDict()
        self._embedding_cache_max_size = 256
        self._session_embedding_encode_calls = 0
        self._session_cache_hits = 0
        self._session_cache_misses = 0

        # In-memory candidate profile store: candidate_id → profile dict
        self.candidates_cache: Dict[str, Dict[str, Any]] = {}

    # ── Public status helpers ─────────────────────────────────────

    def is_semantic_ready(self) -> bool:
        """Returns True when FAISS index is loaded and has vectors."""
        return self._semantic_ready and self._faiss.is_loaded()

    def is_cache_loaded(self) -> bool:
        """Returns True when the candidate profile cache is populated."""
        return self._cache_loaded

    def embedding_cache_stats(self) -> Dict[str, int]:
        """Return process-lifetime query embedding cache counters."""
        with self._embedding_cache_lock:
            return {
                "cache_size": len(self._embedding_cache),
                "session_encode_calls": self._session_embedding_encode_calls,
                "session_cache_hits": self._session_cache_hits,
                "session_cache_misses": self._session_cache_misses,
            }

    # ── Startup loading ───────────────────────────────────────────

    def load_index_and_cache(self, ingestion_service: IngestionService) -> None:
        """
        Loads candidates into the in-memory cache and attempts to load the FAISS index.
        Idempotent and thread-safe — concurrent callers block on a single load.
        """
        with self._load_lock:
            self._load_candidate_cache(ingestion_service)
            self._load_faiss_index()
            if self._embedding_model is not None:
                self._embedding_model._load_model()

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

    # ── Query embedding cache ────────────────────────────────────────────────

    @staticmethod
    def _normalise_query_text(text: str) -> str:
        """Normalize job query text before hashing for cache lookup."""
        return re.sub(r"\s+", " ", text.strip().lower())

    @classmethod
    def _cache_key_for_query(cls, query_text: str) -> str:
        cleaned_jd = cls._normalise_query_text(query_text)
        return hashlib.sha256(cleaned_jd.encode("utf-8")).hexdigest()

    def _get_cached_query_embedding(self, cache_key: str) -> Optional[np.ndarray]:
        with self._embedding_cache_lock:
            cached = self._embedding_cache.get(cache_key)
            if cached is None:
                self._session_cache_misses += 1
                return None
            self._session_cache_hits += 1
            self._embedding_cache.move_to_end(cache_key)
            return cached.copy()

    def _store_query_embedding(self, cache_key: str, embedding: np.ndarray) -> None:
        with self._embedding_cache_lock:
            self._embedding_cache[cache_key] = embedding.copy()
            self._embedding_cache.move_to_end(cache_key)
            while len(self._embedding_cache) > self._embedding_cache_max_size:
                self._embedding_cache.popitem(last=False)

    # ── Retrieval ─────────────────────────────────────────────────

    def retrieve_candidates(
        self,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        top_k: int = 500,
        return_timings: bool = False,
    ):
        """
        Retrieves the top_k most semantically similar candidates for a job query.

        In semantic mode: embeds the job query → FAISS cosine search → profile lookup.
        In keyword mode: returns all cached candidates with score=0.0 (Jaccard in jobs.py).

        Args:
            job_title: Job title string.
            job_description: Full job description.
            required_skills: List of required skill strings.
            top_k: Number of candidates to retrieve (pre-filter pool for hybrid ranking).
            return_timings: Whether to return timing breakdown.

        Returns:
            If return_timings is False:
                List of (candidate_dict, semantic_similarity_score) tuples.
            If return_timings is True:
                Tuple of (results, timings_dict).
        """
        timings = {
            "Query Embedding": 0.0,
            "FAISS Retrieval": 0.0,
            "Embedding Cache Hit": 0.0,
            "Embedding Calls This Request": 0.0,
            "Embedding Calls This Session": float(self._session_embedding_encode_calls),
            "Embedding Cache Hits This Session": float(self._session_cache_hits),
            "Embedding Cache Misses This Session": float(self._session_cache_misses),
        }

        if not self._semantic_ready:
            # Keyword fallback — return all candidates, scores set to 0.0
            results = [(c, 0.0) for c in self.candidates_cache.values()]
            if return_timings:
                return results, timings
            return results

        # Embed the job query
        assert self._embedding_model is not None
        query_text = self._embedding_model.build_job_query_string(
            job_title, job_description, required_skills
        )
        cache_key = self._cache_key_for_query(query_text)
        t_embed_start = time.time()
        query_vec = self._get_cached_query_embedding(cache_key)
        embedding_calls_this_request = 0
        cache_key_short = cache_key[:12]

        if query_vec is not None:
            logger.info("EMBED CACHE HIT key=%s", cache_key_short)
            timings["Embedding Cache Hit"] = 1.0
        else:
            logger.info("EMBED CACHE MISS key=%s", cache_key_short)
            logger.info("Timing - Query embedding generation started")
            query_vec = self._embedding_model.encode(
                query_text,
                batch_size=1,
                normalize=True,  # Normalise for cosine similarity
            )
            embedding_calls_this_request = 1
            self._session_embedding_encode_calls += 1
            self._store_query_embedding(cache_key, query_vec)
        t_embed_end = time.time()
        embed_ms = (t_embed_end - t_embed_start) * 1000
        timings["Query Embedding"] = round(embed_ms, 2)
        timings["Embedding Calls This Request"] = float(embedding_calls_this_request)
        stats = self.embedding_cache_stats()
        timings["Embedding Calls This Session"] = float(stats["session_encode_calls"])
        timings["Embedding Cache Hits This Session"] = float(stats["session_cache_hits"])
        timings["Embedding Cache Misses This Session"] = float(stats["session_cache_misses"])
        logger.info(
            "Timing - Query embedding step: %.2f ms | calls_request=%s calls_session=%s hits_session=%s misses_session=%s",
            embed_ms,
            embedding_calls_this_request,
            stats["session_encode_calls"],
            stats["session_cache_hits"],
            stats["session_cache_misses"],
        )

        # FAISS search
        logger.info("Timing - FAISS retrieval started")
        t_faiss_start = time.time()
        hits = self._faiss.search(query_vec, top_k=top_k)
        t_faiss_end = time.time()
        faiss_ms = (t_faiss_end - t_faiss_start) * 1000
        timings["FAISS Retrieval"] = round(faiss_ms, 2)
        logger.info(f"Timing - FAISS retrieval: {faiss_ms:.2f} ms")

        # Map back to candidate profiles
        results: List[Tuple[Dict[str, Any], float]] = []
        for cand_id, score in hits:
            profile = self.candidates_cache.get(cand_id)
            if profile is not None:
                results.append((profile, float(score)))

        if return_timings:
            return results, timings
        return results

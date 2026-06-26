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

    def embedding_cache_stats(self) -> Dict[str, Any]:
        """Return process-lifetime query embedding cache counters."""
        with self._embedding_cache_lock:
            hits = self._session_cache_hits
            misses = self._session_cache_misses
            total = hits + misses
            rate = round(hits / total, 4) if total > 0 else 0.0
            return {
                "cache_size": len(self._embedding_cache),
                "session_encode_calls": self._session_embedding_encode_calls,
                "session_cache_hits": hits,
                "session_cache_misses": misses,
                "cache_hit_rate": rate,
                "embedding_calls_saved": hits,
            }

    # ── Startup loading ───────────────────────────────────────────

    def load_index_and_cache(self, ingestion_service: IngestionService) -> None:
        """
        Loads candidates into the in-memory cache and attempts to load the FAISS index.
        Idempotent and thread-safe — concurrent callers block on a single load.
        """
        t_wait_start = time.perf_counter()
        with self._load_lock:
            t_wait_end = time.perf_counter()
            wait_ms = (t_wait_end - t_wait_start) * 1000
            if wait_ms > 1.0:
                print(f"[LOCK WAIT] with self._load_lock blocked for {wait_ms:.2f}ms")
            
            self._load_candidate_cache(ingestion_service)
            self._load_faiss_index()
            if self._embedding_model is not None:
                self._embedding_model._load_model()

    def _load_candidate_cache(self, ingestion_service: IngestionService) -> None:
        if self._cache_loaded:
            print("[CACHE REUSE] Cache already loaded in memory.")
            return
        print("[CACHE LOAD] Loading all clean candidate profiles into memory cache...")
        logger.info("Loading all clean candidate profiles into memory cache...")

        # ── Phase 1: Load raw candidate profiles from disk ───────
        t_ingest_start = time.perf_counter()
        candidates = ingestion_service.load_all_candidates(
            limit=-1,
            validate=True,
            preprocess=True,
            exclude_honeypots=True,
            as_dict=True,
        )
        t_ingest_ms = (time.perf_counter() - t_ingest_start) * 1000
        print(f"[CACHE LOAD] Phase 1 — Ingestion: {t_ingest_ms:.2f}ms ({len(candidates):,} candidates)")

        # ── Phase 2: Precompute candidate fields for ranking optimisation ─
        from app.services.ranking.ranking_service import _canonical, _build_candidate_corpus, _SKILL_ALIASES
        from app.ml.title_scorer import _tokenize, _family_of, _seniority_tier

        t_precompute_start = time.perf_counter()
        logger.info("Precomputing candidate fields for ranking optimization...")
        for c in candidates:
            # 1. Precompute title alignment features
            cand_title = c.get("profile", {}).get("current_title", "") or ""
            cand_tok = _tokenize(cand_title)
            c["candidate_title_normalized"] = re.sub(r"\s+", " ", cand_title.lower().strip())
            c["candidate_title_tokens"] = cand_tok
            c["candidate_title_family"] = _family_of(cand_title)
            c["candidate_title_tier"] = _seniority_tier(cand_tok)

            # 2. Precompute skill sets (explicit + matched via aliases substring)
            candidate_normalized_skills = {
                re.sub(r"\s+", " ", (s.get("name", "") or "").lower().strip())
                for s in c.get("skills", [])
                if s.get("name")
            }
            cand_explicit = { _canonical(skill) for skill in candidate_normalized_skills }
            corpus = _build_candidate_corpus(c)

            matched_aliases = set()
            for canonical_skill, aliases in _SKILL_ALIASES.items():
                if canonical_skill in cand_explicit:
                    matched_aliases.add(canonical_skill)
                elif any(alias in corpus for alias in aliases):
                    matched_aliases.add(canonical_skill)

            c["candidate_normalized_skills"] = candidate_normalized_skills
            c["candidate_skill_sets"] = cand_explicit
            c["candidate_explicit_skills"] = cand_explicit
            c["candidate_alias_skills"] = matched_aliases
            c["candidate_corpus"] = corpus
            profile = c.get("profile", {})
            years = float(profile.get("years_of_experience", 0.0) or 0.0)
            c["candidate_experience_match"] = min(years, 15.0) / 15.0

            sig = c.get("redrob_signals", {})
            otw = 1.0 if sig.get("open_to_work_flag", False) else 0.0
            completeness = float(sig.get("profile_completeness_score", 0.0) or 0.0) / 100.0
            response_rate = float(sig.get("recruiter_response_rate", 0.0) or 0.0)
            github_raw = float(sig.get("github_activity_score", -1.0) or -1.0)
            github = max(github_raw, 0.0) / 100.0 if github_raw >= 0 else 0.0
            c["candidate_activity_score"] = (
                0.40 * otw + 0.30 * completeness + 0.20 * response_rate + 0.10 * github
            )

        t_precompute_ms = (time.perf_counter() - t_precompute_start) * 1000
        print(f"[CACHE LOAD] Phase 2 — Precompute: {t_precompute_ms:.2f}ms ({len(candidates):,} candidates)")

        # ── Phase 3: Build lookup dict ───────────────────────────
        t_dict_start = time.perf_counter()
        self.candidates_cache = {c["candidate_id"]: c for c in candidates}
        self._cache_loaded = True
        t_dict_ms = (time.perf_counter() - t_dict_start) * 1000
        print(f"[CACHE LOAD] Phase 3 — Dict build: {t_dict_ms:.2f}ms")

        total_ms = t_ingest_ms + t_precompute_ms + t_dict_ms
        print(f"[CACHE LOAD] TOTAL: {total_ms:.2f}ms  (ingest={t_ingest_ms:.0f} precompute={t_precompute_ms:.0f} dict={t_dict_ms:.0f})")
        logger.info(f"  Cache ready: {len(self.candidates_cache):,} candidates loaded.")

    def _load_faiss_index(self) -> None:
        if self._semantic_ready:
            print("[INDEX REUSE] FAISS index already loaded in memory.")
            return
        if not os.path.exists(self._index_path):
            logger.warning(
                f"FAISS index not found at '{self._index_path}'. "
                "Running in keyword-fallback mode. "
                "Build the index with: python scripts/build_semantic_index.py"
            )
            return
        try:
            print(f"[INDEX LOAD] Loading FAISS index from '{self._index_path}'...")
            logger.info(f"Loading FAISS index from '{self._index_path}'...")
            self._faiss.load(self._index_path)
            self._embedding_model = CandidateEmbeddingModel()
            self._semantic_ready = True
            print("INDEX MODEL:\n"
                  f"{self._embedding_model.model_name}\n"
                  f"{EMBEDDING_DIM}\n"
                  f"normalize=False (at build time)")
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
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

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
            "Candidate Reconstruction": 0.0,
            "Embedding Cache Hit": 0.0,
            "Embedding Calls This Request": 0.0,
            "Embedding Calls This Session": float(self._session_embedding_encode_calls),
            "Embedding Cache Hits This Session": float(self._session_cache_hits),
            "Embedding Cache Misses This Session": float(self._session_cache_misses),
            "Cache Hit Rate": 0.0,
            "Cache Size": float(len(self._embedding_cache)),
            "Embedding Calls Saved": float(self._session_cache_hits),
        }

        if not self._semantic_ready:
            # Keyword fallback — return all candidates, scores set to 0.0
            results = [(c, 0.0) for c in self.candidates_cache.values()]
            if return_timings:
                return results, timings
            return results

        # Embed the job query
        assert self._embedding_model is not None
        # Normalize fields before formatting to prevent whitespace changes from invalidating cache
        job_title_norm = re.sub(r"\s+", " ", job_title.strip().lower())
        job_desc_norm = re.sub(r"\s+", " ", job_description.strip().lower())
        req_skills_norm = [re.sub(r"\s+", " ", s.strip().lower()) for s in required_skills]

        query_text = self._embedding_model.build_job_query_string(
            job_title_norm, job_desc_norm, req_skills_norm
        )
        print("QUERY MODEL:\n"
              f"{self._embedding_model.model_name}\n"
              f"{EMBEDDING_DIM}\n"
              f"normalize=True")

        normalized_query_text = self._normalise_query_text(query_text)
        cache_key = hashlib.sha256(normalized_query_text.encode("utf-8")).hexdigest()
        t_embed_start = time.perf_counter()
        query_vec = self._get_cached_query_embedding(cache_key)
        embedding_calls_this_request = 0

        logger.info("CACHE KEY: %s normalized_chars=%s", cache_key, len(normalized_query_text))
        if query_vec is not None:
            logger.info("CACHE HIT key=%s", cache_key[:12])
            timings["Embedding Cache Hit"] = 1.0
        else:
            logger.info("CACHE MISS key=%s", cache_key[:12])
            logger.info("EMBED START (cache miss — calling encode)")
            query_vec = self._embedding_model.encode(
                query_text,
                batch_size=1,
                normalize=True,  # Normalise for cosine similarity
            )
            logger.info("EMBED END")
            embedding_calls_this_request = 1
            self._session_embedding_encode_calls += 1
            self._store_query_embedding(cache_key, query_vec)
        t_embed_end = time.perf_counter()
        embed_ms = (t_embed_end - t_embed_start) * 1000
        timings["Query Embedding"] = round(embed_ms, 2)
        timings["Embedding Calls This Request"] = float(embedding_calls_this_request)
        stats = self.embedding_cache_stats()
        timings["Embedding Calls This Session"] = float(stats["session_encode_calls"])
        timings["Embedding Cache Hits This Session"] = float(stats["session_cache_hits"])
        timings["Embedding Cache Misses This Session"] = float(stats["session_cache_misses"])
        timings["Cache Hit Rate"] = float(stats["cache_hit_rate"])
        timings["Cache Size"] = float(stats["cache_size"])
        timings["Embedding Calls Saved"] = float(stats["embedding_calls_saved"])
        logger.info(
            "Query Embedding step: %.2fms | cache_hit=%s | calls_request=%s calls_session=%s hits=%s misses=%s",
            embed_ms,
            bool(timings["Embedding Cache Hit"]),
            embedding_calls_this_request,
            stats["session_encode_calls"],
            stats["session_cache_hits"],
            stats["session_cache_misses"],
        )

        # ── FAISS SEARCH (pure index.search call) ──────────────────────────────
        # The timer wraps the entire self._faiss.search() call, which internally
        # logs FAISS_SEARCH_ONLY / METADATA_LOOKUP / POST_PROCESSING sub-timings.
        logger.info("Timing - FAISS retrieval started")
        t_faiss_start = time.perf_counter()
        hits = self._faiss.search(query_vec, top_k=top_k)
        t_faiss_end = time.perf_counter()
        faiss_ms = (t_faiss_end - t_faiss_start) * 1000
        timings["FAISS Retrieval"] = round(faiss_ms, 2)
        logger.info(
            "FAISS outer timer: %.2fms | raw_hits=%s "
            "(sub-breakdown logged by [FAISS] line above)",
            faiss_ms, len(hits),
        )

        # ── CANDIDATE RECONSTRUCTION ────────────────────────────────────────────
        # For each of the top_k FAISS hits, look up the full candidate profile dict
        # from the in-memory candidates_cache (pure dict.get, no I/O, no computation).
        # This step is isolated so its cost is visible separately from FAISS search.
        t_reconstruct_start = time.perf_counter()
        results: List[Tuple[Dict[str, Any], float]] = []
        n_missing = 0
        for cand_id, score in hits:
            profile = self.candidates_cache.get(cand_id)
            if profile is not None:
                results.append((profile, float(score)))
            else:
                n_missing += 1
        t_reconstruct_end = time.perf_counter()
        reconstruct_ms = (t_reconstruct_end - t_reconstruct_start) * 1000
        timings["Candidate Reconstruction"] = round(reconstruct_ms, 2)

        logger.info(
            "CANDIDATE RECONSTRUCTION | faiss_hits=%s → profiles=%s (missing=%s) | %.2fms",
            len(hits), len(results), n_missing, reconstruct_ms,
        )
        print(
            f"[RECONSTRUCT] faiss_hits={len(hits)} -> profiles={len(results)} "
            f"(missing={n_missing}) in {reconstruct_ms:.2f}ms"
        )

        if return_timings:
            return results, timings
        return results

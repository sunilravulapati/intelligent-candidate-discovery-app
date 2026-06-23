"""
Centralised startup state machine for the Semantic Workspace.

Every subsystem sets its flag after loading completes.
The ``ready`` property is derived: ``all([cache, index, model, ranking])``.

Usage::

    from app.core.workspace_state import workspace_state

    workspace_state.set_cache_loaded()
    ...
    if workspace_state.ready:
        ...
"""

import time
import threading
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class WorkspaceState:
    """Thread-safe startup state tracker."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cache_loaded: bool = False
        self._index_loaded: bool = False
        self._model_loaded: bool = False
        self._ranking_loaded: bool = False

        # Detailed startup timing (milliseconds)
        self._startup_start: float | None = None
        self._startup_end: float | None = None
        self._timing: Dict[str, float] = {}

        # Last search performance (populated by jobs.py after each search)
        self.last_search_perf: Dict[str, float] = {}

    # ── Flag setters ──────────────────────────────────────────────

    def mark_startup_begin(self) -> None:
        self._startup_start = time.perf_counter()

    def set_cache_loaded(self, duration_ms: float = 0.0) -> None:
        with self._lock:
            self._cache_loaded = True
            self._timing["candidate_cache_ms"] = round(duration_ms, 2)
        logger.info("WorkspaceState: cache_loaded=True (%.2fms)", duration_ms)

    def set_index_loaded(self, duration_ms: float = 0.0) -> None:
        with self._lock:
            self._index_loaded = True
            self._timing["faiss_index_ms"] = round(duration_ms, 2)
        logger.info("WorkspaceState: index_loaded=True (%.2fms)", duration_ms)

    def set_model_loaded(self, duration_ms: float = 0.0) -> None:
        with self._lock:
            self._model_loaded = True
            self._timing["embedding_model_ms"] = round(duration_ms, 2)
        logger.info("WorkspaceState: model_loaded=True (%.2fms)", duration_ms)

    def set_ranking_loaded(self, duration_ms: float = 0.0) -> None:
        with self._lock:
            self._ranking_loaded = True
            self._timing["ranking_preload_ms"] = round(duration_ms, 2)
        logger.info("WorkspaceState: ranking_loaded=True (%.2fms)", duration_ms)

    def mark_startup_complete(self) -> None:
        self._startup_end = time.perf_counter()
        if self._startup_start is not None:
            self._timing["total_startup_ms"] = round(
                (self._startup_end - self._startup_start) * 1000, 2
            )

    # ── Read-only properties ──────────────────────────────────────

    @property
    def cache_loaded(self) -> bool:
        return self._cache_loaded

    @property
    def index_loaded(self) -> bool:
        return self._index_loaded

    @property
    def model_loaded(self) -> bool:
        return self._model_loaded

    @property
    def ranking_loaded(self) -> bool:
        return self._ranking_loaded

    @property
    def ready(self) -> bool:
        return all([
            self._cache_loaded,
            self._index_loaded,
            self._model_loaded,
            self._ranking_loaded,
        ])

    @property
    def startup_time_ms(self) -> float:
        return self._timing.get("total_startup_ms", 0.0)

    # ── Serialisation ─────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cache_loaded": self._cache_loaded,
            "index_loaded": self._index_loaded,
            "model_loaded": self._model_loaded,
            "ranking_loaded": self._ranking_loaded,
            "ready": self.ready,
            "startup_time_ms": self.startup_time_ms,
            "timing_breakdown": dict(self._timing),
        }


# ── Module-level singleton ────────────────────────────────────────
workspace_state = WorkspaceState()

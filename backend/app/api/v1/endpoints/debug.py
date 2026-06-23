"""
Debug / performance introspection endpoints.

GET /api/v1/debug/performance — returns cached timing metrics from the most
recent search plus startup timing.
"""

from fastapi import APIRouter
from app.core.workspace_state import workspace_state

router = APIRouter()


@router.get("/debug/performance")
def debug_performance():
    """
    Returns performance metrics for the last search execution and startup.

    The values are populated after the first search request completes.
    Before that, only startup_time_ms is available.
    """
    perf = workspace_state.last_search_perf.copy() if workspace_state.last_search_perf else {
        "startup_time_ms": workspace_state.startup_time_ms,
        "embedding_ms": 0,
        "faiss_ms": 0,
        "ranking_ms": 0,
        "explainability_ms": 0,
        "total_ms": 0,
    }
    # Always include current startup_time_ms
    perf["startup_time_ms"] = workspace_state.startup_time_ms
    perf["workspace_state"] = workspace_state.to_dict()
    return perf

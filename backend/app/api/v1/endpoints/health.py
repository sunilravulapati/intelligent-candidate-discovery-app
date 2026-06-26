from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import check_db_status, get_db
from app.services.ingestion.ingestion_service import IngestionService
from app.services.retrieval.retrieval_service import RetrievalService
from app.api import deps
from app.core.workspace_state import workspace_state

router = APIRouter()


@router.get("/health")
def health_check(
    ingestion: IngestionService = Depends(deps.get_ingestion_service),
    retrieval: RetrievalService = Depends(deps.get_retrieval_service)
):
    """
    Checks backend health, database connection, local CSV/JSONL dataset file status,
    and FAISS semantic index status.

    Available immediately during startup — returns granular subsystem status
    from WorkspaceState so the frontend can show progress.
    """
    db_status = check_db_status()
    files_status = ingestion.get_candidate_files_status()

    # Check if we are ready to operate
    system_ready = False
    if db_status["connected"] or files_status.get("active_source") is not None:
        system_ready = True

    semantic_active = retrieval.is_semantic_ready()

    return {
        "status": "ok" if system_ready else "degraded",
        "system_ready": system_ready,
        "database": db_status,
        "datasets": files_status,
        "mode": "Semantic Mode" if semantic_active else "Keyword Fallback",
        "semantic_mode": {
            "active": semantic_active,
            "index_loaded": workspace_state.index_loaded,
            "index_path": retrieval._index_path,
            "candidates_indexed": retrieval._faiss.ntotal if semantic_active else 0
        },
        "startup_status": workspace_state.to_dict(),
    }

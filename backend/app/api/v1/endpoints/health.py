from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import check_db_status, get_db
from app.services.ingestion.ingestion_service import IngestionService
from app.api import deps

router = APIRouter()


@router.get("/health")
def health_check(
    db: Session = Depends(get_db),
    ingestion: IngestionService = Depends(deps.get_ingestion_service)
):
    """
    Checks backend health, database connection, and local CSV/JSONL dataset file status.
    """
    db_status = check_db_status()
    files_status = ingestion.get_candidate_files_status()
    
    # Check if we are ready to operate
    system_ready = False
    if db_status["connected"] or files_status.get("active_source") is not None:
        system_ready = True
        
    return {
        "status": "ok" if system_ready else "degraded",
        "system_ready": system_ready,
        "database": db_status,
        "datasets": files_status,
        "mode": "PostgreSQL-backed" if db_status["connected"] else "CSV-first Fallback"
    }

from contextlib import asynccontextmanager
import logging
import time
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.api import deps
from app.core.workspace_state import workspace_state

logger = logging.getLogger(__name__)


def load_all_background():
    """
    Loads all subsystems in a background thread.

    Each step is individually timed and reported via WorkspaceState.
    The startup thread sets per-component flags so the /health endpoint
    can report granular progress while FastAPI is already accepting requests.
    """
    workspace_state.mark_startup_begin()
    logger.info("Semantic Workspace Initialization Started")
    t_start = time.perf_counter()

    try:
        retrieval = deps.get_retrieval_service()
        ingestion = deps.get_ingestion_service()

        # ── Step 1: Candidate cache ──────────────────────────────
        logger.info("[STARTUP 1/4] Loading candidate cache...")
        t0 = time.perf_counter()
        retrieval._load_candidate_cache(ingestion)
        cache_ms = (time.perf_counter() - t0) * 1000
        workspace_state.set_cache_loaded(cache_ms)
        print(f"[STARTUP 1/4] Candidate cache loaded in {cache_ms:.2f}ms")

        # ── Step 2: FAISS index ──────────────────────────────────
        logger.info("[STARTUP 2/4] Loading FAISS index...")
        t0 = time.perf_counter()
        retrieval._load_faiss_index()
        index_ms = (time.perf_counter() - t0) * 1000
        workspace_state.set_index_loaded(index_ms)
        print(f"[STARTUP 2/4] FAISS index loaded in {index_ms:.2f}ms")

        # ── Step 3: Embedding model ──────────────────────────────
        logger.info("[STARTUP 3/4] Loading embedding model...")
        t0 = time.perf_counter()
        if retrieval._embedding_model is not None:
            retrieval._embedding_model._load_model()
        model_ms = (time.perf_counter() - t0) * 1000
        workspace_state.set_model_loaded(model_ms)
        print(f"[STARTUP 3/4] Embedding model loaded in {model_ms:.2f}ms")

        # ── Step 4: Ranking + Explainability singletons ──────────
        logger.info("[STARTUP 4/4] Pre-warming ranking & explainability services...")
        t0 = time.perf_counter()
        deps.get_ranking_service()
        deps.get_explainability_service()
        ranking_ms = (time.perf_counter() - t0) * 1000
        workspace_state.set_ranking_loaded(ranking_ms)
        print(f"[STARTUP 4/4] Ranking & explainability ready in {ranking_ms:.2f}ms")

        workspace_state.mark_startup_complete()

        t_total = (time.perf_counter() - t_start) * 1000
        logger.info("Semantic Workspace Ready")
        print("\n" + "=" * 60)
        print("STARTUP TIMING BREAKDOWN")
        print("=" * 60)
        print(f"  Candidate Cache  : {cache_ms:>10.2f} ms")
        print(f"  FAISS Index      : {index_ms:>10.2f} ms")
        print(f"  Embedding Model  : {model_ms:>10.2f} ms")
        print(f"  Ranking Preload  : {ranking_ms:>10.2f} ms")
        print(f"  --------------------------------")
        print(f"  Total Startup    : {t_total:>10.2f} ms")
        print("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"Error during background workspace initialization: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start loading in a background thread — FastAPI accepts requests immediately.
    # Health endpoint is available during init; search returns 503 until ready.
    thread = threading.Thread(
        target=load_all_background,
        daemon=True,
    )
    thread.start()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set up CORS middleware for local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes under API v1 prefix (e.g. /api/v1/health, /api/v1/jobs)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Also support top-level /api prefix for ease of integration
app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} API. Please access endpoints under {settings.API_V1_STR}/ or /api/."
    }

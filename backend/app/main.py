from contextlib import asynccontextmanager
import logging
import time
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.api import deps

logger = logging.getLogger(__name__)


def load_all_background():
    logger.info("Semantic Workspace Initialization Started")
    t_start = time.time()
    try:
        retrieval = deps.get_retrieval_service()
        ingestion = deps.get_ingestion_service()

        # Single thread-safe load path (cache + FAISS + embedding model)
        logger.info("Loading candidate cache, FAISS index, and embedding model...")
        t_load_start = time.time()
        retrieval.load_index_and_cache(ingestion)
        logger.info(f"Completed in {(time.time() - t_load_start)*1000:.2f} ms")

        t_total = time.time() - t_start
        logger.info("Semantic Workspace Ready")
        logger.info(f"Total Startup Time: {t_total*1000:.2f} ms")
    except Exception as e:
        logger.error(f"Error during background workspace initialization: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start loading in a background thread to prevent blocking FastAPI startup
    thread = threading.Thread(
        target=load_all_background,
        daemon=True
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

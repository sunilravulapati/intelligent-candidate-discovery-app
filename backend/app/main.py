from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware for local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production specify exact frontend domains
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

from fastapi import APIRouter
from app.api.v1.endpoints import health, jobs, debug

api_router = APIRouter()

# Include health router without API V1 prefix if desired, or under it
api_router.include_router(health.router, tags=["health"])
api_router.include_router(jobs.router, tags=["jobs"])
api_router.include_router(debug.router, tags=["debug"])

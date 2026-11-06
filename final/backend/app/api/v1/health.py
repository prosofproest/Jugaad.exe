"""Health check router.
Provides a simple liveness endpoint.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="Liveness probe")
async def health_check():
    """Return a minimal health payload.
    No external dependencies are checked – this endpoint should always return 200.
    """
    return {"status": "ok"}


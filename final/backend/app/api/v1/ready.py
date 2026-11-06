"""Readiness probe router.
Checks that critical dependencies (DB, Cloudinary) are reachable.
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from backend.app.database import engine

router = APIRouter()

@router.get("/", summary="Readiness probe")
async def readiness_check():
    """Return 200 when DB connection succeeds, otherwise 503.
    Cloudinary check is stubbed – in production you would ping the API.
    """
    try:
        # Simple query to ensure DB is up
        with engine.connect() as conn:
            conn.execute("SELECT 1")
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    # Stub Cloudinary check – always OK for now
    return {"status": "ready"}


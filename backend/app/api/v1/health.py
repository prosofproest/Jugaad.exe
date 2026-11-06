"""Health endpoints.

Health reports the process state only. It must never imply that models,
forecasts or data are valid.
"""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


def health_payload() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "time": datetime.now(UTC).isoformat(),
    }


@router.get("/health")
def health() -> dict[str, str]:
    return health_payload()

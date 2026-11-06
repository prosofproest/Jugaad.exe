"""Version 1 API router.

Every route that exposes data or initiates work must be routed through this
table. An unrouted endpoint is dead code; a routed endpoint without an
authorisation dependency is a defect.
"""

from fastapi import APIRouter

from app.api.v1 import (
    advisories,
    alerts,
    assessments,
    auth,
    conversations,
    forecast,
    health,
    map,
    observations,
    review,
)

api_router = APIRouter()

# Health
api_router.include_router(health.router)

# Auth & Admin Auth
api_router.include_router(auth.router)
if hasattr(auth, "admin_router"):
    api_router.include_router(auth.admin_router)

# Observations & Review
api_router.include_router(observations.router)
api_router.include_router(review.router)

# Advisories
api_router.include_router(advisories.router)
if hasattr(advisories, "admin_router"):
    api_router.include_router(advisories.admin_router)

# Alerts
api_router.include_router(alerts.router)
if hasattr(alerts, "admin_router"):
    api_router.include_router(alerts.admin_router)

# Forecast
api_router.include_router(forecast.router)
if hasattr(forecast, "admin_router"):
    api_router.include_router(forecast.admin_router)

# Conversations & Assessments
api_router.include_router(conversations.router)
api_router.include_router(assessments.router)

# Map
api_router.include_router(map.router)

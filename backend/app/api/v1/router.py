"""Version 1 API router.

Feature routers are added here as each module lands. A route without an
authorisation dependency is a defect.
"""

from fastapi import APIRouter

from app.api.v1 import advisories, alerts, auth, conversations, forecast, health, observations, review

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(auth.admin_router)
api_router.include_router(observations.router)
api_router.include_router(review.router)
api_router.include_router(advisories.router)
api_router.include_router(advisories.admin_router)
api_router.include_router(alerts.router)
api_router.include_router(alerts.admin_router)
api_router.include_router(forecast.router)
api_router.include_router(forecast.admin_router)
api_router.include_router(conversations.router)

"""Version 1 API router.

Feature routers are added here as each module lands. A route without an
authorisation dependency is a defect.
"""

from fastapi import APIRouter

from app.api.v1 import assessments, conversations, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(conversations.router)
api_router.include_router(assessments.router)

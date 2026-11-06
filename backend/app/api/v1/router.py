"""Version 1 API router.

Feature routers are added here as each module lands. A route without an
authorisation dependency is a defect.
"""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    advisories,
    assessments,
    auth,
    conversations,
    health,
    map,
    me,
    uploads,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(admin.router)
api_router.include_router(conversations.router)
api_router.include_router(uploads.router)
api_router.include_router(assessments.router)
api_router.include_router(advisories.router)
api_router.include_router(map.router)

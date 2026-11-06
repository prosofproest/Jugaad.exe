"""FastAPI application entry point.

Modular monolith: one deployable app, explicit internal module boundaries.
See ``docs-context/architecture-context.md`` for the invariants.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import health_payload
from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "PS-03 decision-support API. Photo assessment and area outlook are "
        "separate outputs and are never merged."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Unauthenticated liveness probe used by the web client and deploy checks."""
    return health_payload()

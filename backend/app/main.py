"""FastAPI application entry point.

Modular monolith: one deployable app, explicit internal module boundaries.
See ``docs-context/architecture-context.md`` for the invariants.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import health_payload
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import install_error_handlers
from app.core.request_context import RequestContextMiddleware, configure_logging

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    if settings.seed_reference_data:
        from app.db.session import init_db

        init_db(seed=True)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "PS-03 decision-support API. Photo assessment and area outlook are "
        "separate outputs and are never merged."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
)
app.add_middleware(RequestContextMiddleware)

install_error_handlers(app)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Unauthenticated liveness probe used by the web client and deploy checks."""

    return health_payload()

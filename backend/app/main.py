"""FastAPI application entry point.

Modular monolith: one deployable app, explicit internal module boundaries.
See ``final/docs-context/architecture-context.md`` for the invariants and
``final/TRD.md`` §4 for module ownership.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import health_payload
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.modules.identity.dependencies import get_identity_service

OPENAPI_TAGS = [
    {"name": "health", "description": "Process liveness only."},
    {
        "name": "auth",
        "description": (
            "Phone OTP for farmers, email/password + TOTP for staff, rotating "
            "refresh tokens and logout."
        ),
    },
    {
        "name": "me",
        "description": "Authenticated profile, versioned consent, export and privacy requests.",
    },
    {
        "name": "admin",
        "description": (
            "Admin-only user provisioning, audited record views, role/status changes, "
            "retention jobs and aggregate-only exports."
        ),
    },
    {
        "name": "conversations",
        "description": (
            "Conversational capture: upload an image, send a message and receive "
            "a structured assessment card. Demo replies are labelled `is_demo`; "
            "no real model is served in this phase."
        ),
    },
    {
        "name": "videos",
        "description": (
            "Video reading: upload a short clip, sample bounded frames, track motion "
            "regions and return per-frame photo assessments plus a non-diagnostic "
            "summary. The shipped detector is demo-only and every reading requires "
            "human review."
        ),
    },
]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    # Construct identity now so production misconfiguration and the one-time
    # admin bootstrap fail at startup rather than on the first request.
    get_identity_service()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    docs_enabled = settings.docs_enabled and not settings.is_production

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "PS-03 decision-support API. Photo assessment and area outlook are "
            "separate outputs and are never merged. Error responses follow the "
            "problem-details envelope documented in final/TRD.md §7.2."
        ),
        openapi_tags=OPENAPI_TAGS,
        docs_url="/docs" if docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs_enabled else None,
        lifespan=lifespan,
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
    )

    register_error_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        """Unauthenticated liveness probe used by the web client and deploy checks."""
        return health_payload()

    return app


app = create_app()

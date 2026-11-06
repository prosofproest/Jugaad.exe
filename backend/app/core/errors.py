"""RFC 7807-style error envelope used by every endpoint.

``code`` is stable and machine-readable; clients branch on it, never on
``detail`` (``final/TRD.md`` §7.2). The envelope never leaks stack traces,
SQL or model internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import request_id_var

PROBLEM_MEDIA_TYPE = "application/problem+json"
_ERROR_BASE = "https://api.ps03.local/errors/"


@dataclass
class ApiError(Exception):
    """A deliberately raised, client-safe error."""

    code: str
    title: str
    status: int = 400
    detail: str | None = None
    retryable: bool = False
    fields: list[dict[str, str]] = field(default_factory=list)


def _status_code_for(code: str) -> str:
    return code.strip().lower().replace("-", "_").replace(" ", "_")


def _payload(
    *,
    code: str,
    title: str,
    status: int,
    detail: str | None,
    retryable: bool = False,
    fields: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "type": f"{_ERROR_BASE}{_status_code_for(code)}",
        "title": title,
        "status": status,
        "code": code,
        "detail": detail,
        "request_id": request_id_var.get(),
        "retryable": retryable,
        "fields": fields or [],
    }


def _response(payload: dict[str, Any]) -> JSONResponse:
    return JSONResponse(
        status_code=payload["status"],
        content=payload,
        media_type=PROBLEM_MEDIA_TYPE,
    )


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return _response(
        _payload(
            code=exc.code,
            title=exc.title,
            status=exc.status,
            detail=exc.detail,
            retryable=exc.retryable,
            fields=exc.fields,
        )
    )


async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    status = exc.status_code
    try:
        phrase = HTTPStatus(status).phrase
    except ValueError:
        phrase = "Request failed"
    return _response(
        _payload(
            code=_status_code_for(phrase),
            title=phrase,
            status=status,
            detail=exc.detail if isinstance(exc.detail, str) else None,
        )
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    fields = [
        {
            "field": ".".join(str(part) for part in error.get("loc", [])),
            "message": str(error.get("msg", "invalid value")),
        }
        for error in exc.errors()
    ]
    return _response(
        _payload(
            code="validation_error",
            title="Request validation failed",
            status=422,
            detail="One or more fields are invalid.",
            fields=fields,
        )
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log the type only; the client never receives internals.
    import logging

    logging.getLogger("app.errors").exception(
        "unhandled_exception", extra={"path": request.url.path}
    )
    return _response(
        _payload(
            code="internal_error",
            title="Internal server error",
            status=500,
            detail=None,
        )
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

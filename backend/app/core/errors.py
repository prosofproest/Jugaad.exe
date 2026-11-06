"""Domain error types and the single RFC 7807-style API error envelope."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_context import get_request_id


class ApiError(Exception):
    """A stable, machine-readable API failure.

    Routers and services raise this instead of constructing ad-hoc responses.
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        title: str,
        *,
        detail: str | None = None,
        fields: list[dict[str, Any]] | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(detail or title)
        self.status_code = status_code
        self.code = code
        self.title = title
        self.detail = detail
        self.fields = fields
        self.retryable = retryable


def error_body(
    *,
    status: int,
    code: str,
    title: str,
    detail: str | None = None,
    fields: list[dict[str, Any]] | None = None,
    retryable: bool = False,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": f"https://api.ps03.local/errors/{code.replace('_', '-')}",
        "title": title,
        "status": status,
        "code": code,
        "detail": detail or title,
        "request_id": get_request_id(),
        "retryable": retryable,
    }
    if fields:
        body["fields"] = fields
    return body


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, error: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content=error_body(
                status=error.status_code,
                code=error.code,
                title=error.title,
                detail=error.detail,
                fields=error.fields,
                retryable=error.retryable,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
        fields = [
            {
                "field": ".".join(str(part) for part in item.get("loc", [])),
                "message": item.get("msg", "Invalid value"),
                "type": item.get("type", "value_error"),
            }
            for item in error.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_body(
                status=422,
                code="validation_error",
                title="Request validation failed",
                fields=fields,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, error: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if error.status_code == 404 else "http_error"
        if error.status_code == 401:
            code = "unauthorized"
        elif error.status_code == 403:
            code = "forbidden"
        return JSONResponse(
            status_code=error.status_code,
            content=error_body(
                status=error.status_code,
                code=code,
                title=str(error.detail) if error.detail else "Request failed",
            ),
            headers=getattr(error, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, error: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=error_body(
                status=500,
                code="internal_error",
                title="Internal server error",
                retryable=True,
            ),
        )

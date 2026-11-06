"""Request-scoped identifiers and structured JSON logging.

Logs carry identifiers and outcomes only: no user text, phone numbers, image
bytes or coordinates.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_request_id: ContextVar[str] = ContextVar("request_id", default="-")
_logger = logging.getLogger("ps03")


def get_request_id() -> str:
    return _request_id.get()


def log_event(event: str, level: int = logging.INFO, **fields: object) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": logging.getLevelName(level).lower(),
        "event": event,
        "request_id": get_request_id(),
        **fields,
    }
    _logger.log(level, json.dumps(record, default=str, separators=(",", ":")))


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.handlers = [handler]
    _logger.setLevel(logging.INFO)
    _logger.propagate = False


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        incoming = request.headers.get("X-Request-ID")
        request_id = incoming if incoming and len(incoming) <= 128 else f"req_{uuid4().hex}"
        token = _request_id.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            log_event(
                "http.request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=round((time.perf_counter() - started) * 1000, 2),
            )
            return response
        finally:
            _request_id.reset(token)

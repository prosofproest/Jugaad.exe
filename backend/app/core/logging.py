"""Structured JSON logging.

Rules (``docs-context/TRD.md`` §15.1 and ``code-standards.md``):

- one JSON event per line;
- every event carries ``request_id`` when one exists;
- log state transitions, never payloads, image bytes, phone numbers,
  coordinates, free-text notes or secrets.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# LogRecord attributes that are not part of a structured event by default.
_RESERVED = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    """Render a log record as one JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "event": record.getMessage(),
        }

        request_id = getattr(record, "request_id", None) or request_id_var.get()
        if request_id:
            event["request_id"] = request_id

        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                event[key] = value

        if record.exc_info:
            # Type only: stack traces and payloads stay out of logs.
            event["error_type"] = getattr(record.exc_info[0], "__name__", "Exception")

        return json.dumps(event, default=str, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    """Install the JSON formatter on the root logger exactly once."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Access logs duplicate request-level events; keep them out of the stream.
    logging.getLogger("uvicorn.access").disabled = True

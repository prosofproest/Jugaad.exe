"""Shared request/response helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Page[T](BaseModel):
    items: list[T]
    next_cursor: str | None = None


class MessageResponse(BaseModel):
    message: str


class CursorQuery(BaseModel):
    cursor: str | None = None
    limit: int = Field(default=25, ge=1, le=100)


def iso(value: datetime | None) -> str | None:
    """Serialise an aware UTC datetime with an explicit ``Z`` suffix."""
    if value is None:
        return None
    return value.astimezone().isoformat().replace("+00:00", "Z")


RELATIVE_NOT_DIAGNOSIS = (
    "This is an assistive photo assessment, not a diagnosis. "
    "Only a qualified person can confirm what is affecting a plant."
)

AREA_NOT_CONFIRMED = (
    "This is an area-level early warning, not confirmation of disease in your field. "
    "A low band does not mean the area is disease-free."
)


def info(message: str, **extra: Any) -> dict[str, Any]:
    return {"message": message, **extra}

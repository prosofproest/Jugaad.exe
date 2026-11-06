"""UTC time helpers.

Every timestamp in the system is UTC. API payloads serialise ISO-8601 with a
trailing ``Z``; the database stores the same text form. Nothing in the domain
layer calls ``datetime.now()`` without a timezone.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def utcnow() -> datetime:
    """Current time as a timezone-aware UTC datetime."""

    return datetime.now(timezone.utc)


def to_iso(value: datetime) -> str:
    """Serialise a datetime as ``YYYY-MM-DDTHH:MM:SSZ`` in UTC."""

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 timestamp, accepting ``Z`` and naive input as UTC."""

    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_date(value: datetime) -> str:
    """Return the UTC calendar date as ``YYYY-MM-DD``."""

    return value.astimezone(timezone.utc).date().isoformat()


def hours_between(earlier: datetime, later: datetime) -> float:
    """Signed hour difference ``later - earlier``."""

    return (later - earlier).total_seconds() / 3600.0


def days_between(earlier: datetime, later: datetime) -> float:
    """Signed day difference ``later - earlier``."""

    return (later - earlier).total_seconds() / 86400.0


def day_floor(value: datetime) -> datetime:
    """Midnight UTC of the given instant."""

    return value.astimezone(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def add_days(value: datetime, days: int) -> datetime:
    return value + timedelta(days=days)

"""Append-only audit events shared by approval and delivery workflows.

Audit rows are the record of who approved, published, withdrew, sent or
suppressed something. They are stored separately from the business objects so
an update to a delivery status cannot rewrite history.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

Clock = Callable[[], datetime]


class AuditEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    actor_id: str | None
    at: datetime
    detail: dict[str, str] = Field(default_factory=dict)


class AuditLog:
    """In-memory append-only audit log.

    The database implementation will be an insert-only table. The contract here
    is the same: no update and no delete method exists.
    """

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock if clock is not None else (lambda: datetime.now(UTC))
        self._events: list[AuditEvent] = []
        self._lock = Lock()

    def record(
        self,
        event_type: str,
        *,
        entity_type: str,
        entity_id: str,
        actor_id: str | None = None,
        detail: dict[str, object] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=f"aud_{uuid4().hex}",
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            at=self._clock(),
            detail={key: str(value) for key, value in (detail or {}).items()},
        )
        with self._lock:
            self._events.append(event)
        return event

    def events(self) -> list[AuditEvent]:
        with self._lock:
            return list(self._events)

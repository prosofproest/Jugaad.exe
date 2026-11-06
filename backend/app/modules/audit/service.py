"""Append-only audit events."""

from __future__ import annotations

from typing import Any

from app.core.request_context import get_request_id
from app.db.models import AuditEvent, User
from sqlalchemy.orm import Session


def record_audit(
    db: Session,
    *,
    action: str,
    actor: User | None = None,
    actor_id: str | None = None,
    actor_role: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    reason: str | None = None,
    detail: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_id=actor.id if actor else actor_id,
        actor_role=actor.active_role if actor else actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        reason=reason,
        request_id=get_request_id(),
        detail=detail or {},
    )
    db.add(event)
    return event

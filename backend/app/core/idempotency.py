"""Idempotency helpers for client-generated request keys."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.db.models import IdempotencyRecord


def find_existing(
    db: Session, *, user_id: str, scope: str, key: str
) -> IdempotencyRecord | None:
    return db.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.user_id == user_id,
            IdempotencyRecord.scope == scope,
            IdempotencyRecord.key == key,
        )
    )


def remember(
    db: Session,
    *,
    user_id: str,
    scope: str,
    key: str,
    entity_id: str,
    request_hash: str | None = None,
) -> IdempotencyRecord:
    record = IdempotencyRecord(
        user_id=user_id,
        scope=scope,
        key=key,
        entity_id=entity_id,
        request_hash=request_hash,
    )
    db.add(record)
    return record


def ensure_key_matches(
    db: Session, *, user_id: str, scope: str, key: str, entity_id: str
) -> None:
    """Raise if a key was already used for a different entity."""

    record = find_existing(db, user_id=user_id, scope=scope, key=key)
    if record is not None and record.entity_id != entity_id:
        raise ApiError(
            409,
            "idempotency_conflict",
            "Idempotency key was reused for a different request",
        )

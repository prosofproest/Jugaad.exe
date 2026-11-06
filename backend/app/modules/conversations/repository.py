"""Persistence for conversational capture.

Every function takes an explicit ``Session`` so the API owns the transaction
boundary and tests can run against SQLite. The previous process-local store is
gone: conversations, messages, uploads and review requests survive a restart.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.conversations.orm import (
    ConversationRow,
    ImageUploadRow,
    MessageEventRow,
    MessageRow,
    ReviewRequestRow,
)


def utcnow() -> datetime:
    return datetime.now(UTC)


def create_conversation(session: Session, *, owner_id: str, title: str) -> ConversationRow:
    now = utcnow()
    row = ConversationRow(
        id=_new_id("conv"),
        owner_id=owner_id,
        title=title,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )
    session.add(row)
    session.flush()
    return row


def list_conversations(session: Session, *, owner_id: str) -> list[ConversationRow]:
    statement = (
        select(ConversationRow)
        .where(
            ConversationRow.owner_id == owner_id,
            ConversationRow.deleted_at.is_(None),
        )
        .order_by(ConversationRow.last_message_at.desc())
    )
    return list(session.scalars(statement))


def get_conversation(
    session: Session, *, conversation_id: str, owner_id: str
) -> ConversationRow | None:
    return session.scalar(
        select(ConversationRow).where(
            ConversationRow.id == conversation_id,
            ConversationRow.owner_id == owner_id,
            ConversationRow.deleted_at.is_(None),
        )
    )


def delete_conversation(session: Session, row: ConversationRow) -> None:
    row.deleted_at = utcnow()
    row.updated_at = row.deleted_at
    session.flush()


def list_messages(session: Session, *, conversation_id: str) -> list[MessageRow]:
    statement = (
        select(MessageRow)
        .where(MessageRow.conversation_id == conversation_id)
        .order_by(MessageRow.sequence.asc(), MessageRow.created_at.asc())
    )
    return list(session.scalars(statement))


def get_message(session: Session, *, conversation_id: str, message_id: str) -> MessageRow | None:
    return session.scalar(
        select(MessageRow).where(
            MessageRow.conversation_id == conversation_id,
            MessageRow.id == message_id,
        )
    )


def find_turn(
    session: Session, *, conversation_id: str, client_message_id: str
) -> tuple[MessageRow, MessageRow] | None:
    user = session.scalar(
        select(MessageRow).where(
            MessageRow.conversation_id == conversation_id,
            MessageRow.client_message_id == client_message_id,
        )
    )
    if user is None:
        return None
    assistant = session.scalar(
        select(MessageRow).where(
            MessageRow.conversation_id == conversation_id,
            MessageRow.turn_id == client_message_id,
            MessageRow.role == "assistant",
        )
    )
    if assistant is None:
        return None
    return user, assistant


def _next_sequence(session: Session, conversation_id: str) -> int:
    current = session.scalar(
        select(func.max(MessageRow.sequence)).where(MessageRow.conversation_id == conversation_id)
    )
    return int(current or 0) + 1


def append_turn(
    session: Session,
    *,
    conversation: ConversationRow,
    user_message: MessageRow,
    assistant_message: MessageRow,
) -> None:
    start = _next_sequence(session, conversation.id)
    user_message.sequence = start
    assistant_message.sequence = start + 1
    session.add_all([user_message, assistant_message])
    conversation.last_message_at = assistant_message.created_at
    conversation.updated_at = assistant_message.created_at
    session.flush()


def add_event(
    session: Session,
    *,
    conversation_id: str,
    message_id: str,
    event_type: str,
    detail: dict | None = None,
) -> MessageEventRow:
    row = MessageEventRow(
        id=_new_id("evt"),
        conversation_id=conversation_id,
        message_id=message_id,
        event_type=event_type,
        detail=detail,
        created_at=utcnow(),
    )
    session.add(row)
    session.flush()
    return row


def create_upload(
    session: Session,
    *,
    upload_id: str,
    owner_id: str,
    filename: str,
    content_type: str,
    size_bytes: int,
    sha256: str,
    storage_path: str,
    width: int,
    height: int,
    laplacian_variance: float,
    mean_luma: float,
    clipped_fraction: float,
    plant_presence: float,
    quality_result: str,
    quality_flags: list[str],
    quality_gate_version: str,
) -> ImageUploadRow:
    row = ImageUploadRow(
        id=upload_id,
        owner_id=owner_id,
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        sha256=sha256,
        storage_path=storage_path,
        width=width,
        height=height,
        laplacian_variance=laplacian_variance,
        mean_luma=mean_luma,
        clipped_fraction=clipped_fraction,
        plant_presence=plant_presence,
        quality_result=quality_result,
        quality_flags=quality_flags,
        quality_gate_version=quality_gate_version,
        created_at=utcnow(),
    )
    session.add(row)
    session.flush()
    return row


def get_upload(session: Session, *, upload_id: str, owner_id: str) -> ImageUploadRow | None:
    return session.scalar(
        select(ImageUploadRow).where(
            ImageUploadRow.id == upload_id,
            ImageUploadRow.owner_id == owner_id,
        )
    )


def get_review_for_message(session: Session, *, message_id: str) -> ReviewRequestRow | None:
    return session.scalar(select(ReviewRequestRow).where(ReviewRequestRow.message_id == message_id))


def create_review_request(
    session: Session,
    *,
    conversation_id: str,
    message_id: str,
    owner_id: str,
    reason: str | None,
) -> tuple[ReviewRequestRow, bool]:
    existing = get_review_for_message(session, message_id=message_id)
    if existing is not None:
        return existing, False

    row = ReviewRequestRow(
        id=_new_id("rev"),
        conversation_id=conversation_id,
        message_id=message_id,
        owner_id=owner_id,
        status="requested",
        reason=reason,
        created_at=utcnow(),
    )
    session.add(row)
    session.flush()
    return row, True


def _new_id(prefix: str) -> str:
    from uuid import uuid4

    return f"{prefix}_{uuid4().hex}"

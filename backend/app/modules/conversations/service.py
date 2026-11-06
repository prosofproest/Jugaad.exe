"""Conversation service (spec 08).

The service owns the turn: validate the referenced upload, run the pluggable
assessment engine, persist the user message and the append-only assistant reply
in one transaction, and expose review requests. It never fabricates a result:
the engine decides the state, and a missing upload is a client error.

The demo engine is selected by ``APP_CHAT_ENGINE`` and always marks its output
``is_demo``. Photo assessment and area outlook stay separate; nothing here
produces or merges an outlook.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.modules.conversations import repository as repo
from app.modules.conversations.engine import (
    AssessmentEngine,
    UploadContext,
    get_assessment_engine,
)
from app.modules.conversations.media import inspect_image, store_image
from app.modules.conversations.models import (
    Assessment,
    Candidate,
    Conversation,
    ImageRefOut,
    Message,
    MessageCreate,
    ReviewRequestOut,
    SendResult,
    UploadDescriptor,
)
from app.modules.conversations.orm import ConversationRow, ImageUploadRow, MessageRow

OWNER_ID = "demo_user"
NOT_A_DIAGNOSIS = "Assistive photo assessment — not a diagnosis."


class ConversationNotFoundError(Exception):
    """Raised when a conversation does not exist for the caller."""


class MessageNotFoundError(Exception):
    """Raised when a message does not exist in the conversation."""


class UploadNotFoundError(Exception):
    """Raised when an upload does not exist for the caller."""


class InvalidReviewTargetError(Exception):
    """Raised when a review is requested for a message that cannot take one."""


def _id(prefix: str) -> str:
    from uuid import uuid4

    return f"{prefix}_{uuid4().hex}"


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime) -> datetime:
    """SQLite returns naive timestamps; treat stored values as UTC."""

    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _conversation(row: ConversationRow) -> Conversation:
    return Conversation(
        conversation_id=row.id,
        owner_id=row.owner_id,
        title=row.title,
        created_at=_aware(row.created_at),
        last_message_at=_aware(row.last_message_at),
    )


def _image_ref(row: ImageUploadRow) -> ImageRefOut:
    return ImageRefOut(
        upload_id=row.id,
        filename=row.filename,
        content_type=row.content_type,
        content_hash=row.sha256,
        width=row.width,
        height=row.height,
        quality_result=row.quality_result,
        quality_flags=list(row.quality_flags or []),
        preview_url=f"/v1/uploads/{row.id}",
    )


def _review(row) -> ReviewRequestOut:
    return ReviewRequestOut(
        review_request_id=row.id,
        conversation_id=row.conversation_id,
        message_id=row.message_id,
        status=row.status,
        reason=row.reason,
        submitted_at=_aware(row.created_at),
    )


def _message(session: Session, row: MessageRow) -> Message:
    assessment = Assessment.model_validate(row.assessment) if row.assessment else None
    image = ImageRefOut.model_validate(row.image) if row.image else None
    review = repo.get_review_for_message(session, message_id=row.id)
    return Message(
        message_id=row.id,
        conversation_id=row.conversation_id,
        role=row.role,
        kind=row.kind,
        text=row.text,
        client_message_id=row.client_message_id,
        observation_id=row.observation_id,
        image=image,
        assessment=assessment,
        review_request=_review(review) if review else None,
        next_steps=list(row.next_steps or []),
        created_at=_aware(row.created_at),
        is_demo=row.is_demo,
    )


def _require_conversation(session: Session, conversation_id: str) -> ConversationRow:
    row = repo.get_conversation(session, conversation_id=conversation_id, owner_id=OWNER_ID)
    if row is None:
        raise ConversationNotFoundError(conversation_id)
    return row


def create_conversation(session: Session, title: str | None) -> Conversation:
    row = repo.create_conversation(
        session,
        owner_id=OWNER_ID,
        title=title or "New conversation",
    )
    return _conversation(row)


def list_conversations(session: Session) -> list[Conversation]:
    return [_conversation(row) for row in repo.list_conversations(session, owner_id=OWNER_ID)]


def get_conversation(session: Session, conversation_id: str) -> Conversation:
    return _conversation(_require_conversation(session, conversation_id))


def delete_conversation(session: Session, conversation_id: str) -> None:
    repo.delete_conversation(session, _require_conversation(session, conversation_id))


def list_messages(session: Session, conversation_id: str) -> list[Message]:
    _require_conversation(session, conversation_id)
    return [
        _message(session, row)
        for row in repo.list_messages(session, conversation_id=conversation_id)
    ]


def _build_assessment(
    result,
    *,
    generated_at: datetime,
    observation_id: str | None,
) -> Assessment:
    return Assessment(
        state=result.state,
        reason_code=result.reason_code,
        reason_text=result.reason_text,
        quality_flag=result.quality_flag,
        quality_flags=list(result.quality_flags),
        candidates=[Candidate(**candidate) for candidate in result.candidates],
        confidence_band=result.confidence_band,
        calibrated=result.calibrated,
        model_version=result.model_version,
        generated_at=generated_at,
        is_demo=result.is_demo,
        observation_id=observation_id,
        error_code=result.error_code,
        retryable=result.retryable,
    )


def send_message(
    session: Session,
    conversation_id: str,
    payload: MessageCreate,
    idempotency_key: str,
    *,
    engine: AssessmentEngine | None = None,
) -> SendResult:
    conversation = _require_conversation(session, conversation_id)

    existing = repo.find_turn(
        session,
        conversation_id=conversation_id,
        client_message_id=payload.client_message_id,
    )
    if existing is not None:
        user, assistant = existing
        return SendResult(
            user_message=_message(session, user),
            assistant_message=_message(session, assistant),
        )

    upload_row: ImageUploadRow | None = None
    image_payload: dict | None = None
    if payload.image is not None and payload.image.upload_id is not None:
        upload_row = repo.get_upload(
            session,
            upload_id=payload.image.upload_id,
            owner_id=OWNER_ID,
        )
        if upload_row is None:
            raise UploadNotFoundError(payload.image.upload_id)
        image_payload = _image_ref(upload_row).model_dump(mode="json")

    engine = engine or get_assessment_engine()
    upload_context = (
        UploadContext(
            upload_id=upload_row.id,
            sha256=upload_row.sha256,
            width=upload_row.width,
            height=upload_row.height,
            quality_result=upload_row.quality_result,
            quality_flags=tuple(upload_row.quality_flags or []),
        )
        if upload_row is not None
        else None
    )
    result = engine.assess(
        upload=upload_context,
        crop_id=payload.crop_id,
        context=payload.text,
    )

    now = _now()
    assessment = _build_assessment(
        result,
        generated_at=now,
        observation_id=upload_row.id if upload_row is not None else None,
    )
    assistant_text = f"{NOT_A_DIAGNOSIS} {result.reason_text}".strip()

    user_message = MessageRow(
        id=_id("msg"),
        conversation_id=conversation_id,
        role="user",
        kind="image" if upload_row is not None else "text",
        text=payload.text,
        client_message_id=payload.client_message_id,
        turn_id=payload.client_message_id,
        observation_id=upload_row.id if upload_row is not None else None,
        image=image_payload,
        is_demo=False,
        created_at=now,
    )
    assistant_message = MessageRow(
        id=_id("msg"),
        conversation_id=conversation_id,
        role="assistant",
        kind="assessment" if result.state == "assessed" else result.state,
        text=assistant_text,
        turn_id=payload.client_message_id,
        observation_id=upload_row.id if upload_row is not None else None,
        assessment=assessment.model_dump(mode="json"),
        next_steps=list(result.next_steps),
        is_demo=result.is_demo,
        created_at=now,
    )
    repo.append_turn(
        session,
        conversation=conversation,
        user_message=user_message,
        assistant_message=assistant_message,
    )
    repo.add_event(
        session,
        conversation_id=conversation_id,
        message_id=assistant_message.id,
        event_type="assessment_completed",
        detail={
            "state": result.state,
            "reason_code": result.reason_code,
            "model_version": result.model_version,
            "is_demo": result.is_demo,
        },
    )

    return SendResult(
        user_message=_message(session, user_message),
        assistant_message=_message(session, assistant_message),
    )


def retry_message(session: Session, conversation_id: str, message_id: str) -> Message:
    """Return the stored message. A retry never fabricates a new result.

    Re-running an assessment is a new user turn (a retake), not an edit of the
    append-only assistant reply.
    """

    _require_conversation(session, conversation_id)
    row = repo.get_message(session, conversation_id=conversation_id, message_id=message_id)
    if row is None:
        raise MessageNotFoundError(message_id)
    return _message(session, row)


def request_review(
    session: Session,
    conversation_id: str,
    message_id: str,
    reason: str | None,
) -> ReviewRequestOut:
    _require_conversation(session, conversation_id)
    message = repo.get_message(session, conversation_id=conversation_id, message_id=message_id)
    if message is None:
        raise MessageNotFoundError(message_id)
    if message.role != "assistant":
        raise InvalidReviewTargetError(message_id)

    row, created = repo.create_review_request(
        session,
        conversation_id=conversation_id,
        message_id=message_id,
        owner_id=OWNER_ID,
        reason=reason,
    )
    if created:
        repo.add_event(
            session,
            conversation_id=conversation_id,
            message_id=message_id,
            event_type="review_requested",
            detail={"review_request_id": row.id},
        )
    return _review(row)


def create_upload(
    session: Session,
    *,
    settings: Settings,
    filename: str,
    content_type: str,
    data: bytes,
) -> UploadDescriptor:
    inspected = inspect_image(data, content_type)
    upload_id = _id("up")
    storage_path = store_image(settings, OWNER_ID, upload_id, content_type, data)
    row = repo.create_upload(
        session,
        upload_id=upload_id,
        owner_id=OWNER_ID,
        filename=filename[:255] or "upload",
        content_type=content_type,
        size_bytes=len(data),
        sha256=inspected.content_hash,
        storage_path=storage_path,
        width=inspected.width,
        height=inspected.height,
        laplacian_variance=inspected.metrics.laplacian_variance,
        mean_luma=inspected.metrics.mean_luma,
        clipped_fraction=inspected.metrics.clipped_fraction,
        plant_presence=inspected.metrics.plant_presence,
        quality_result=inspected.quality.result,
        quality_flags=list(inspected.quality.flags),
        quality_gate_version=inspected.quality.gate_version,
    )
    return upload_descriptor(row)


def upload_descriptor(row: ImageUploadRow) -> UploadDescriptor:
    return UploadDescriptor(
        upload_id=row.id,
        filename=row.filename,
        content_type=row.content_type,
        content_hash=row.sha256,
        size_bytes=row.size_bytes,
        width=row.width,
        height=row.height,
        quality_result=row.quality_result,
        quality_flags=list(row.quality_flags or []),
        quality_gate_version=row.quality_gate_version,
        preview_url=f"/v1/uploads/{row.id}",
        created_at=_aware(row.created_at),
        is_demo=True,
    )


def get_upload_row(session: Session, upload_id: str) -> ImageUploadRow:
    row = repo.get_upload(session, upload_id=upload_id, owner_id=OWNER_ID)
    if row is None:
        raise UploadNotFoundError(upload_id)
    return row

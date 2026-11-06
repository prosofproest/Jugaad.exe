"""Database-backed conversational capture.

A conversation wraps the same photo-assessment pipeline as the report flow. It
never diagnoses, never merges the area outlook into a reply and never invents a
result when an upload is incomplete. Assistant messages are append-only.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.db.base import new_id
from app.db.models import (
    Conversation,
    ImageAsset,
    Message,
    MessageAttachment,
    MessageEvent,
    ReviewRequest,
    User,
)
from app.modules.assessment import service as assessment_service
from app.modules.audit.service import record_audit
from app.modules.identity import service as identity_service
from app.modules.media import storage
from app.modules.observations import service as observation_service

CHAT_TEMPLATE_VERSION = "chat-template-2026-11-v1"
NOT_DIAGNOSIS = "Assistive photo assessment, not a diagnosis."
REASON_TEXT = {
    "low_resolution": "The photo is too small to assess reliably. Retake it closer to the leaves.",
    "blur": "The photo is too blurry to assess. Hold the phone steady and retake.",
    "metadata_missing": "The photo details are incomplete, so it cannot be assessed. Retake it.",
    "unsupported_type": "That image format cannot be assessed. Use a JPEG or PNG photo.",
    "insufficient_quality": "The image did not pass the quality check. Retake it in good light.",
    "unsupported_crop": "This crop is not yet supported for photo assessment.",
    "unsupported_target": "No validated target exists for this crop yet.",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id(prefix: str) -> str:
    return new_id(prefix)


def _conversation(db: Session, conversation_id: str) -> Conversation:
    row = db.get(Conversation, conversation_id)
    if row is None or row.deleted_at is not None:
        raise ApiError(404, "not_found", "Conversation not found")
    return row


def _require_read(
    db: Session, *, user: User, conversation: Conversation, reason: str | None
) -> None:
    if conversation.owner_id == user.id:
        return
    roles = identity_service.active_roles(db, user.id)
    if "admin" in roles:
        if not reason:
            raise ApiError(
                400,
                "reason_required",
                "Admin access to a conversation requires a reason",
            )
    elif "extension_worker" in roles:
        if conversation.area_code is None or conversation.area_code not in {
            row.geo_code for row in _area_assignments(db, user.id)
        }:
            raise ApiError(403, "forbidden", "This conversation is outside your area")
        if not reason:
            raise ApiError(
                400,
                "reason_required",
                "Staff access to a conversation requires a reason",
            )
    else:
        raise ApiError(403, "forbidden", "This conversation belongs to another user")
    record_audit(
        db,
        action="conversation.staff_viewed",
        actor=user,
        entity_type="conversation",
        entity_id=conversation.id,
        reason=reason,
    )


def _area_assignments(db: Session, user_id: str):
    from app.db.models import UserAreaAssignment

    return db.scalars(
        select(UserAreaAssignment).where(UserAreaAssignment.user_id == user_id)
    ).all()


def create_conversation(
    db: Session,
    *,
    user: User,
    title: str | None,
    crop_code: str | None,
    area_code: str | None,
) -> Conversation:
    conversation = Conversation(
        owner_id=user.id,
        title=(title or "New conversation")[:300],
        crop_code=crop_code,
        area_code=area_code,
        last_message_at=None,
        unread_count=0,
    )
    db.add(conversation)
    db.flush()
    record_audit(
        db,
        action="conversation.created",
        actor=user,
        entity_type="conversation",
        entity_id=conversation.id,
    )
    return conversation


def _last_message(db: Session, conversation_id: str) -> Message | None:
    return db.scalar(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
    )


def serialize_conversation(db: Session, conversation: Conversation) -> dict:
    last = _last_message(db, conversation.id)
    return {
        "conversation_id": conversation.id,
        "title": conversation.title,
        "crop_code": conversation.crop_code,
        "area_code": conversation.area_code,
        "created_at": conversation.created_at.isoformat(),
        "last_message_at": conversation.last_message_at.isoformat()
        if conversation.last_message_at
        else None,
        "unread_count": conversation.unread_count,
        "last_message": (
            {
                "message_id": last.id,
                "role": last.role,
                "kind": last.kind,
                "preview": (last.text or "")[:140],
                "created_at": last.created_at.isoformat(),
                "is_demo": last.is_demo,
            }
            if last
            else None
        ),
    }


def list_conversations(db: Session, *, user: User, limit: int = 50) -> dict:
    rows = db.scalars(
        select(Conversation)
        .where(
            Conversation.owner_id == user.id,
            Conversation.deleted_at.is_(None),
        )
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    ).all()
    return {"items": [serialize_conversation(db, row) for row in rows]}


def get_conversation(
    db: Session, *, user: User, conversation_id: str, reason: str | None
) -> dict:
    conversation = _conversation(db, conversation_id)
    _require_read(db, user=user, conversation=conversation, reason=reason)
    return serialize_conversation(db, conversation)


def serialize_message(message: Message, attachments: list[ImageAsset]) -> dict:
    payload = dict(message.payload or {})
    return {
        "message_id": message.id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "kind": message.kind,
        "text": message.text,
        "client_message_id": message.client_message_id,
        "reply_to_message_id": message.reply_to_message_id,
        "observation_id": message.observation_id,
        "assessment_id": message.assessment_id,
        "assessment": payload.get("assessment"),
        "next_steps": payload.get("next_steps", []),
        "reason_code": payload.get("reason_code"),
        "reason_text": payload.get("reason_text"),
        "model_version": message.model_version,
        "template_version": payload.get("template_version"),
        "generated_at": message.generated_at.isoformat()
        if message.generated_at
        else None,
        "created_at": message.created_at.isoformat(),
        "is_demo": message.is_demo,
        "attachments": [
            {
                "image_id": image.id,
                "content_type": image.mime,
                "upload_status": image.upload_status,
            }
            for image in attachments
        ],
        "notice": NOT_DIAGNOSIS,
    }


def _attachments(db: Session, message_id: str) -> list[ImageAsset]:
    return db.scalars(
        select(ImageAsset)
        .join(MessageAttachment, MessageAttachment.image_id == ImageAsset.id)
        .where(MessageAttachment.message_id == message_id)
    ).all()


def list_messages(
    db: Session, *, user: User, conversation_id: str, reason: str | None
) -> dict:
    conversation = _conversation(db, conversation_id)
    _require_read(db, user=user, conversation=conversation, reason=reason)
    if conversation.owner_id == user.id and conversation.unread_count:
        conversation.unread_count = 0
    rows = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    ).all()
    return {
        "conversation_id": conversation.id,
        "items": [
            serialize_message(row, _attachments(db, row.id)) for row in rows
        ],
        "assessment_and_outlook_separate": True,
    }


def _assistant_payload(
    db: Session, observation, image: ImageAsset | None
) -> dict:
    if image is None:
        return {
            "kind": "text",
            "text": "Attach a photo of the affected plant to get an assistive photo assessment.",
            "payload": {
                "template_version": CHAT_TEMPLATE_VERSION,
                "next_steps": ["add_image"],
            },
            "is_demo": False,
            "model_version": CHAT_TEMPLATE_VERSION,
            "generated_at": _now(),
        }

    if not storage.exists(image.storage_key):
        return {
            "kind": "queued",
            "text": "The photo is saved and will be assessed when the upload completes.",
            "payload": {
                "template_version": CHAT_TEMPLATE_VERSION,
                "next_steps": ["wait", "view_queue"],
                "queued_at": _now().isoformat(),
            },
            "is_demo": False,
            "model_version": CHAT_TEMPLATE_VERSION,
            "generated_at": _now(),
        }

    if image.upload_status != "uploaded":
        image.upload_status = "uploaded"
    assessment = assessment_service.assessment_payload(db, observation)
    if assessment.get("state") in {"unavailable", "pending_upload", "failed"}:
        quality = assessment_service.run_quality_gate(db, image)
        prediction = assessment_service.run_assessment(
            db, observation=observation, image=image, quality=quality
        )
        assessment = assessment_service.assessment_payload(db, observation)
        assessment_id = prediction.id
    else:
        prediction = assessment_service.latest_prediction(db, observation.id)
        assessment_id = prediction.id if prediction else None

    state = assessment.get("state")
    reason_code = assessment.get("abstention_reason")
    if state == "abstained":
        quality = assessment.get("quality") or {}
        flags = list(quality.get("flags") or [])
        reason_code = flags[0] if flags else reason_code or "insufficient_quality"
        reason_text = REASON_TEXT.get(
            reason_code, "The photo could not be assessed reliably. Retake it."
        )
        text = f"{NOT_DIAGNOSIS} {reason_text}"
        next_steps = ["retake", "request_review"]
        kind = "unsupported_crop" if reason_code == "unsupported_crop" else "abstained"
    elif state == "assessed":
        text = f"{NOT_DIAGNOSIS} Open the card to see what the model may be seeing."
        next_steps = ["add_context", "request_review", "read_advisory"]
        kind = "assessed"
    else:
        reason_code = reason_code or "assessment_failed"
        reason_text = REASON_TEXT.get(
            reason_code, "The assessment did not complete. Retry when connected."
        )
        text = f"{NOT_DIAGNOSIS} {reason_text}"
        next_steps = ["retry"]
        kind = "failed"

    return {
        "kind": kind,
        "text": text,
        "payload": {
            "template_version": CHAT_TEMPLATE_VERSION,
            "assessment": assessment,
            "reason_code": reason_code,
            "reason_text": REASON_TEXT.get(reason_code),
            "next_steps": next_steps,
            "assessment_and_outlook_separate": True,
        },
        "is_demo": bool(assessment.get("is_demo")),
        "model_version": assessment.get("model_version"),
        "generated_at": _now(),
        "assessment_id": assessment_id,
    }


def _resolve_observation(
    db: Session,
    *,
    user: User,
    conversation: Conversation,
    observation_id: str | None,
    crop_code: str | None,
    area_code: str | None,
    client_message_id: str,
) -> object | None:
    if observation_id:
        observation = observation_service.writable_observation(
            db, user, observation_id
        )
        if conversation.crop_code is None:
            conversation.crop_code = observation.crop_code
        if conversation.area_code is None:
            conversation.area_code = observation.area_code
        return observation

    crop = crop_code or conversation.crop_code
    area = area_code or conversation.area_code
    if not crop or not area:
        return None
    observation, _created = observation_service.create_observation(
        db,
        user=user,
        client_report_id=f"chat:{client_message_id}"[:128],
        crop_code=crop,
        area_code=area,
        variety=None,
        growth_stage=None,
        notes=None,
        captured_at=None,
        subject_user_id=None,
        idempotency_key=f"chat-observation:{client_message_id}"[:200],
    )
    conversation.crop_code = crop
    conversation.area_code = area
    return observation


def send_message(
    db: Session,
    *,
    user: User,
    conversation_id: str,
    idempotency_key: str,
    client_message_id: str,
    text: str | None,
    observation_id: str | None,
    image_id: str | None,
    crop_code: str | None,
    area_code: str | None,
) -> dict:
    conversation = _conversation(db, conversation_id)
    _require_read(db, user=user, conversation=conversation, reason=None)
    if conversation.owner_id != user.id:
        raise ApiError(403, "forbidden", "Only the owner can send messages")

    if client_message_id != idempotency_key:
        raise ApiError(
            422,
            "idempotency_mismatch",
            "Idempotency-Key must match client_message_id",
        )

    existing = db.scalar(
        select(Message).where(
            Message.conversation_id == conversation.id,
            Message.client_message_id == client_message_id,
        )
    )
    if existing is not None:
        assistant = db.scalar(
            select(Message).where(
                Message.conversation_id == conversation.id,
                Message.reply_to_message_id == existing.id,
            )
        )
        if assistant is not None:
            return {
                "user_message": serialize_message(
                    existing, _attachments(db, existing.id)
                ),
                "assistant_message": serialize_message(
                    assistant, _attachments(db, assistant.id)
                ),
                "idempotent_replay": True,
            }

    observation = _resolve_observation(
        db,
        user=user,
        conversation=conversation,
        observation_id=observation_id,
        crop_code=crop_code,
        area_code=area_code,
        client_message_id=client_message_id,
    )

    image: ImageAsset | None = None
    if image_id:
        if observation is None:
            raise ApiError(
                422,
                "observation_required",
                "An observation is required before attaching an image",
            )
        image = db.get(ImageAsset, image_id)
        if image is None or image.observation_id != observation.id:
            raise ApiError(404, "not_found", "Image not found for this observation")

    user_message = Message(
        id=_id("msg"),
        conversation_id=conversation.id,
        role="user",
        kind="image" if image else "text",
        text=text[:2000] if text else None,
        client_message_id=client_message_id,
        observation_id=observation.id if observation else None,
        payload={"template_version": CHAT_TEMPLATE_VERSION},
        is_demo=False,
        created_at=_now(),
    )
    db.add(user_message)
    db.flush()
    if image is not None:
        db.add(
            MessageAttachment(
                message_id=user_message.id,
                image_id=image.id,
            )
        )

    reply = _assistant_payload(db, observation, image) if observation else {
        "kind": "text",
        "text": "Add the crop and approximate area, then attach a photo.",
        "payload": {
            "template_version": CHAT_TEMPLATE_VERSION,
            "next_steps": ["add_context", "add_image"],
        },
        "is_demo": False,
        "model_version": CHAT_TEMPLATE_VERSION,
        "generated_at": _now(),
    }
    assistant_message = Message(
        id=_id("msg"),
        conversation_id=conversation.id,
        role="assistant",
        kind=reply["kind"],
        text=reply["text"],
        reply_to_message_id=user_message.id,
        observation_id=observation.id if observation else None,
        assessment_id=reply.get("assessment_id"),
        model_version=reply.get("model_version"),
        generated_at=reply.get("generated_at"),
        payload=reply["payload"],
        is_demo=bool(reply.get("is_demo")),
        created_at=_now(),
    )
    db.add(assistant_message)
    conversation.last_message_at = assistant_message.created_at
    conversation.updated_at = assistant_message.created_at
    db.add(
        MessageEvent(
            message_id=user_message.id,
            type="sent",
            payload={"client_message_id": client_message_id},
        )
    )
    db.add(
        MessageEvent(
            message_id=assistant_message.id,
            type=f"reply.{reply['kind']}",
            payload={
                "model_version": assistant_message.model_version,
                "is_demo": assistant_message.is_demo,
            },
        )
    )
    record_audit(
        db,
        action="conversation.message_sent",
        actor=user,
        entity_type="conversation",
        entity_id=conversation.id,
        detail={
            "message_id": user_message.id,
            "reply_kind": assistant_message.kind,
            "observation_id": user_message.observation_id,
            "has_image": image is not None,
        },
    )
    db.flush()
    return {
        "user_message": serialize_message(user_message, _attachments(db, user_message.id)),
        "assistant_message": serialize_message(
            assistant_message, _attachments(db, assistant_message.id)
        ),
        "idempotent_replay": False,
    }


def request_review(
    db: Session, *, user: User, conversation_id: str, message_id: str
) -> dict:
    conversation = _conversation(db, conversation_id)
    _require_read(db, user=user, conversation=conversation, reason=None)
    if conversation.owner_id != user.id:
        raise ApiError(403, "forbidden", "Only the owner can request review")
    source = db.get(Message, message_id)
    if source is None or source.conversation_id != conversation.id:
        raise ApiError(404, "not_found", "Message not found")
    if source.observation_id is None:
        raise ApiError(
            422,
            "observation_required",
            "Send a photo before requesting expert review",
        )
    observation = observation_service.readable_observation(
        db, user, source.observation_id
    )
    review_request = observation_service.request_review(
        db, user=user, observation=observation, reason="requested from chat"
    )
    assistant = Message(
        id=_id("msg"),
        conversation_id=conversation.id,
        role="assistant",
        kind="review_requested",
        text="Expert review requested. You can follow the case status here.",
        reply_to_message_id=source.id,
        observation_id=observation.id,
        model_version=CHAT_TEMPLATE_VERSION,
        generated_at=_now(),
        payload={
            "template_version": CHAT_TEMPLATE_VERSION,
            "review_request_id": review_request.id,
            "status": review_request.status,
            "submitted_at": review_request.created_at.isoformat(),
            "next_steps": ["view_status"],
        },
        is_demo=False,
        created_at=_now(),
    )
    db.add(assistant)
    conversation.last_message_at = assistant.created_at
    conversation.updated_at = assistant.created_at
    db.add(
        MessageEvent(
            message_id=assistant.id,
            type="review_requested",
            payload={"review_request_id": review_request.id},
        )
    )
    db.flush()
    return {
        "review_request_id": review_request.id,
        "status": review_request.status,
        "message": serialize_message(assistant, []),
    }


def retry_message(
    db: Session, *, user: User, conversation_id: str, message_id: str
) -> dict:
    conversation = _conversation(db, conversation_id)
    _require_read(db, user=user, conversation=conversation, reason=None)
    if conversation.owner_id != user.id:
        raise ApiError(403, "forbidden", "Only the owner can retry a message")
    source = db.get(Message, message_id)
    if source is None or source.conversation_id != conversation.id:
        raise ApiError(404, "not_found", "Message not found")
    if source.role != "user":
        raise ApiError(422, "invalid_retry", "Only a user message can be retried")

    image = None
    attachments = _attachments(db, source.id)
    if attachments:
        image = attachments[0]
    if source.observation_id is None or image is None:
        reply = {
            "kind": "failed",
            "text": "There is no uploaded photo to retry. Send a new photo.",
            "payload": {
                "template_version": CHAT_TEMPLATE_VERSION,
                "error_code": "nothing_to_retry",
                "retryable": False,
                "next_steps": ["add_image"],
            },
            "is_demo": False,
            "model_version": CHAT_TEMPLATE_VERSION,
            "generated_at": _now(),
        }
    else:
        observation = observation_service.writable_observation(
            db, user, source.observation_id
        )
        reply = _assistant_payload(db, observation, image)
    assistant = Message(
        id=_id("msg"),
        conversation_id=conversation.id,
        role="assistant",
        kind=reply["kind"],
        text=reply["text"],
        reply_to_message_id=source.id,
        observation_id=source.observation_id,
        assessment_id=reply.get("assessment_id"),
        model_version=reply.get("model_version"),
        generated_at=reply.get("generated_at"),
        payload=reply["payload"],
        is_demo=bool(reply.get("is_demo")),
        created_at=_now(),
    )
    db.add(assistant)
    conversation.last_message_at = assistant.created_at
    conversation.updated_at = assistant.created_at
    db.add(
        MessageEvent(
            message_id=assistant.id,
            type="retried",
            payload={"source_message_id": source.id, "kind": reply["kind"]},
        )
    )
    db.flush()
    return {
        "message_id": assistant.id,
        "kind": assistant.kind,
        "assistant_message": serialize_message(assistant, []),
        "retryable": bool(reply["payload"].get("retryable", reply["kind"] != "assessed")),
    }


def delete_conversation(db: Session, *, user: User, conversation_id: str) -> None:
    conversation = _conversation(db, conversation_id)
    if conversation.owner_id != user.id:
        raise ApiError(403, "forbidden", "This conversation belongs to another user")
    message_ids = [
        row.id
        for row in db.scalars(
            select(Message).where(Message.conversation_id == conversation.id)
        ).all()
    ]
    if message_ids:
        for row in db.scalars(
            select(MessageAttachment).where(
                MessageAttachment.message_id.in_(message_ids)
            )
        ).all():
            db.delete(row)
        for row in db.scalars(
            select(MessageEvent).where(MessageEvent.message_id.in_(message_ids))
        ).all():
            db.delete(row)
        for row in db.scalars(
            select(Message).where(Message.id.in_(message_ids))
        ).all():
            db.delete(row)
    conversation.deleted_at = _now()
    conversation.updated_at = _now()
    record_audit(
        db,
        action="conversation.deleted",
        actor=user,
        entity_type="conversation",
        entity_id=conversation.id,
        detail={"messages_deleted": len(message_ids)},
    )


def list_events(
    db: Session, *, user: User, conversation_id: str, reason: str | None
) -> dict:
    conversation = _conversation(db, conversation_id)
    _require_read(db, user=user, conversation=conversation, reason=reason)
    message_ids = [
        row.id
        for row in db.scalars(
            select(Message).where(Message.conversation_id == conversation.id)
        ).all()
    ]
    if not message_ids:
        return {"items": []}
    rows = db.scalars(
        select(MessageEvent)
        .where(MessageEvent.message_id.in_(message_ids))
        .order_by(MessageEvent.created_at)
    ).all()
    return {
        "items": [
            {
                "event_id": row.id,
                "message_id": row.message_id,
                "type": row.type,
                "payload": row.payload,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }

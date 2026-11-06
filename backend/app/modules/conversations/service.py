"""Conversation service.

This is the scaffold implementation of the chat wrapper described in
``final/feature-specs/08-conversational-capture.md``. It creates one user
message and one structured assistant reply, and is idempotent on
``client_message_id``.

No image model is connected. Every assistant reply is marked ``is_demo`` and
explains that assessment is not available yet. It never emits a diagnosis or
chemical advice.
"""

from datetime import datetime, timezone
from uuid import uuid4

from app.modules.conversations.models import (
    Assessment,
    Conversation,
    Message,
    MessageCreate,
    SendResult,
)
from app.modules.conversations.store import store

OWNER_ID = "demo_user"
DEMO_MODEL_VERSION = "scaffold-demo-0.1"


class ConversationNotFoundError(Exception):
    """Raised when a conversation does not exist for the caller."""


class MessageNotFoundError(Exception):
    """Raised when a message does not exist in the conversation."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def create_conversation(title: str | None) -> Conversation:
    now = _now()
    conversation = Conversation(
        conversation_id=_id("conv"),
        owner_id=OWNER_ID,
        title=title or "New conversation",
        created_at=now,
        last_message_at=now,
    )
    return store.create(conversation)


def list_conversations() -> list[Conversation]:
    return store.list_for_owner(OWNER_ID)


def get_conversation(conversation_id: str) -> Conversation:
    record = store.get(conversation_id)
    if record is None or record.conversation.owner_id != OWNER_ID:
        raise ConversationNotFoundError(conversation_id)
    return record.conversation


def delete_conversation(conversation_id: str) -> None:
    get_conversation(conversation_id)
    store.delete(conversation_id)


def list_messages(conversation_id: str) -> list[Message]:
    get_conversation(conversation_id)
    return store.messages(conversation_id)


def _demo_reply(conversation_id: str, has_image: bool) -> Message:
    now = _now()
    if has_image:
        reason_code = "demo_mode"
        reason_text = (
            "Demo scaffold only: the image was received but no assessment model "
            "is connected yet."
        )
    else:
        reason_code = "no_image"
        reason_text = "No photo was attached, so there is nothing to assess."

    assessment = Assessment(
        state="abstained",
        reason_code=reason_code,
        reason_text=reason_text,
        model_version=DEMO_MODEL_VERSION,
        generated_at=now,
        is_demo=True,
    )
    return Message(
        message_id=_id("msg"),
        conversation_id=conversation_id,
        role="assistant",
        kind="abstained",
        text=(
            "Assistive photo assessment — not a diagnosis. "
            + reason_text
        ),
        assessment=assessment,
        next_steps=["retake"],
        created_at=now,
        is_demo=True,
    )


def send_message(
    conversation_id: str, payload: MessageCreate, idempotency_key: str
) -> SendResult:
    get_conversation(conversation_id)

    existing = store.find_by_client_id(conversation_id, payload.client_message_id)
    if existing is not None:
        user_id, assistant_id = existing
        user = store.message(conversation_id, user_id)
        assistant = store.message(conversation_id, assistant_id)
        if user is not None and assistant is not None:
            return SendResult(user_message=user, assistant_message=assistant)

    now = _now()
    user_message = Message(
        message_id=_id("msg"),
        conversation_id=conversation_id,
        role="user",
        kind="image" if payload.image is not None else "text",
        text=payload.text,
        client_message_id=payload.client_message_id,
        created_at=now,
    )
    assistant_message = _demo_reply(
        conversation_id, has_image=payload.image is not None
    )
    store.append(
        conversation_id,
        [user_message, assistant_message],
        client_message_id=payload.client_message_id,
    )
    return SendResult(user_message=user_message, assistant_message=assistant_message)


def retry_message(conversation_id: str, message_id: str) -> Message:
    get_conversation(conversation_id)
    message = store.message(conversation_id, message_id)
    if message is None:
        raise MessageNotFoundError(message_id)
    # The scaffold does not fabricate a new result. A retry returns the stored
    # message; the real pipeline re-runs the queued job.
    return message

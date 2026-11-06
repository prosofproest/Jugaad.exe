"""Chat routes (spec 08 §7).

Conversations, messages and review requests are persisted through the session
dependency. Every route requires an authenticated caller and is scoped to that
caller's own records (``owner_id`` is the token principal, never a fixed demo
user). Image bytes never travel in the JSON message: the client uploads first
(``POST /v1/uploads``) and references the returned ``upload_id``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.db.session import get_session
from app.modules.conversations import service
from app.modules.conversations.models import (
    Conversation,
    ConversationCreate,
    Message,
    MessageCreate,
    ReviewRequestCreate,
    ReviewRequestOut,
    SendResult,
)
from app.modules.identity.dependencies import get_current_context
from app.modules.identity.service import AuthContext

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _not_found(code: str, title: str) -> ApiError:
    return ApiError(code=code, title=title, status=404)


@router.get("", response_model=list[Conversation])
def list_conversations(
    session: Session = Depends(get_session),
    context: AuthContext = Depends(get_current_context),
) -> list[Conversation]:
    return service.list_conversations(session, context.user.user_id)


@router.post("", response_model=Conversation, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    session: Session = Depends(get_session),
    context: AuthContext = Depends(get_current_context),
) -> Conversation:
    return service.create_conversation(session, context.user.user_id, payload.title)


@router.get("/{conversation_id}", response_model=Conversation)
def get_conversation(
    conversation_id: str,
    session: Session = Depends(get_session),
    context: AuthContext = Depends(get_current_context),
) -> Conversation:
    try:
        return service.get_conversation(session, conversation_id, context.user.user_id)
    except service.ConversationNotFoundError as error:
        raise _not_found("conversation_not_found", "Conversation not found") from error


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    session: Session = Depends(get_session),
    context: AuthContext = Depends(get_current_context),
) -> None:
    try:
        service.delete_conversation(session, conversation_id, context.user.user_id)
    except service.ConversationNotFoundError as error:
        raise _not_found("conversation_not_found", "Conversation not found") from error


@router.get("/{conversation_id}/messages", response_model=list[Message])
def list_messages(
    conversation_id: str,
    session: Session = Depends(get_session),
    context: AuthContext = Depends(get_current_context),
) -> list[Message]:
    try:
        return service.list_messages(session, conversation_id, context.user.user_id)
    except service.ConversationNotFoundError as error:
        raise _not_found("conversation_not_found", "Conversation not found") from error


@router.post("/{conversation_id}/messages", response_model=SendResult)
def send_message(
    conversation_id: str,
    payload: MessageCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1),
    session: Session = Depends(get_session),
    context: AuthContext = Depends(get_current_context),
) -> SendResult:
    if idempotency_key != payload.client_message_id:
        raise ApiError(
            code="idempotency_key_mismatch",
            title="Idempotency-Key must match client_message_id",
            status=400,
        )
    try:
        return service.send_message(
            session,
            conversation_id,
            payload,
            idempotency_key,
            context.user.user_id,
        )
    except service.ConversationNotFoundError as error:
        raise _not_found("conversation_not_found", "Conversation not found") from error
    except service.UploadNotFoundError as error:
        raise _not_found("upload_not_found", "Upload not found") from error


@router.post("/{conversation_id}/messages/{message_id}/retry", response_model=Message)
def retry_message(
    conversation_id: str,
    message_id: str,
    session: Session = Depends(get_session),
    context: AuthContext = Depends(get_current_context),
) -> Message:
    try:
        return service.retry_message(session, conversation_id, message_id, context.user.user_id)
    except service.ConversationNotFoundError as error:
        raise _not_found("conversation_not_found", "Conversation not found") from error
    except service.MessageNotFoundError as error:
        raise _not_found("message_not_found", "Message not found") from error


@router.post(
    "/{conversation_id}/messages/{message_id}/review",
    response_model=ReviewRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def request_review(
    conversation_id: str,
    message_id: str,
    payload: ReviewRequestCreate | None = None,
    session: Session = Depends(get_session),
    context: AuthContext = Depends(get_current_context),
) -> ReviewRequestOut:
    try:
        return service.request_review(
            session,
            conversation_id,
            message_id,
            payload.reason if payload is not None else None,
            context.user.user_id,
        )
    except service.ConversationNotFoundError as error:
        raise _not_found("conversation_not_found", "Conversation not found") from error
    except service.MessageNotFoundError as error:
        raise _not_found("message_not_found", "Message not found") from error
    except service.InvalidReviewTargetError as error:
        raise ApiError(
            code="invalid_review_target",
            title="Only an assistant assessment can be sent for review",
            status=400,
        ) from error

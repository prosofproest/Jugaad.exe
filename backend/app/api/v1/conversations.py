"""Chat routes.

Scaffold scope: in-memory conversations and a labelled demo reply. The real
implementation adds authentication, ownership checks, presigned media and the
inference pipeline; see ``final/feature-specs/08-conversational-capture.md``.
"""

from fastapi import APIRouter, Header, HTTPException, status

from app.modules.conversations import service
from app.modules.conversations.models import (
    Conversation,
    ConversationCreate,
    Message,
    MessageCreate,
    SendResult,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[Conversation])
def list_conversations() -> list[Conversation]:
    return service.list_conversations()


@router.post("", response_model=Conversation, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate) -> Conversation:
    return service.create_conversation(payload.title)


@router.get("/{conversation_id}", response_model=Conversation)
def get_conversation(conversation_id: str) -> Conversation:
    try:
        return service.get_conversation(conversation_id)
    except service.ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found") from error


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: str) -> None:
    try:
        service.delete_conversation(conversation_id)
    except service.ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found") from error


@router.get("/{conversation_id}/messages", response_model=list[Message])
def list_messages(conversation_id: str) -> list[Message]:
    try:
        return service.list_messages(conversation_id)
    except service.ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found") from error


@router.post("/{conversation_id}/messages", response_model=SendResult)
def send_message(
    conversation_id: str,
    payload: MessageCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1),
) -> SendResult:
    if idempotency_key != payload.client_message_id:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key must match client_message_id",
        )
    try:
        return service.send_message(conversation_id, payload, idempotency_key)
    except service.ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found") from error


@router.post("/{conversation_id}/messages/{message_id}/retry", response_model=Message)
def retry_message(conversation_id: str, message_id: str) -> Message:
    try:
        return service.retry_message(conversation_id, message_id)
    except service.ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found") from error
    except service.MessageNotFoundError as error:
        raise HTTPException(status_code=404, detail="Message not found") from error

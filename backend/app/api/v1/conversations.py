"""Conversation routes for web and mobile chat."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    require_idempotency_key,
)
from app.db.models import User
from app.db.session import get_db
from app.modules.conversations import service

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    crop_code: str | None = Field(default=None, max_length=60)
    area_code: str | None = Field(default=None, max_length=64)


class MessageCreate(BaseModel):
    client_message_id: str = Field(min_length=8, max_length=128)
    text: str | None = Field(default=None, max_length=2000)
    observation_id: str | None = None
    image_id: str | None = None
    crop_code: str | None = None
    area_code: str | None = None


@router.get("")
def list_conversations(
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return service.list_conversations(db, user=user, limit=limit)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    conversation = service.create_conversation(
        db,
        user=user,
        title=payload.title,
        crop_code=payload.crop_code,
        area_code=payload.area_code,
    )
    db.commit()
    return service.serialize_conversation(db, conversation)


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str,
    reason: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return service.get_conversation(
        db, user=user, conversation_id=conversation_id, reason=reason
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service.delete_conversation(db, user=user, conversation_id=conversation_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{conversation_id}/messages")
def list_messages(
    conversation_id: str,
    reason: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = service.list_messages(
        db, user=user, conversation_id=conversation_id, reason=reason
    )
    db.commit()
    return result


@router.post("/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
def send_message(
    conversation_id: str,
    payload: MessageCreate,
    response: Response,
    idempotency_key: str = Depends(require_idempotency_key),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = service.send_message(
        db,
        user=user,
        conversation_id=conversation_id,
        idempotency_key=idempotency_key,
        client_message_id=payload.client_message_id,
        text=payload.text,
        observation_id=payload.observation_id,
        image_id=payload.image_id,
        crop_code=payload.crop_code,
        area_code=payload.area_code,
    )
    db.commit()
    if result.get("idempotent_replay"):
        response.status_code = status.HTTP_200_OK
    return result


@router.post("/{conversation_id}/messages/{message_id}/retry")
def retry_message(
    conversation_id: str,
    message_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = service.retry_message(
        db, user=user, conversation_id=conversation_id, message_id=message_id
    )
    db.commit()
    return result


@router.post("/{conversation_id}/messages/{message_id}/review-request")
def request_review(
    conversation_id: str,
    message_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = service.request_review(
        db, user=user, conversation_id=conversation_id, message_id=message_id
    )
    db.commit()
    return result


@router.get("/{conversation_id}/events")
def list_events(
    conversation_id: str,
    reason: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return service.list_events(
        db, user=user, conversation_id=conversation_id, reason=reason
    )

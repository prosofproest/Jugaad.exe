"""Request and response models for conversational capture."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ImageRef(BaseModel):
    """A reference to an uploaded image.

    The real API accepts a presigned upload id; this scaffold accepts metadata
    only and never stores image bytes.
    """

    filename: str | None = Field(default=None, max_length=255)
    content_type: str | None = Field(default=None, max_length=100)
    content_hash: str | None = Field(default=None, max_length=128)


class MessageCreate(BaseModel):
    client_message_id: str = Field(min_length=1, max_length=128)
    text: str | None = Field(default=None, max_length=1000)
    image: ImageRef | None = None


class Candidate(BaseModel):
    label: str
    score: float


class Assessment(BaseModel):
    state: Literal["assessed", "abstained", "unsupported_crop", "failed"]
    reason_code: str | None = None
    reason_text: str | None = None
    candidates: list[Candidate] = Field(default_factory=list)
    confidence_band: str | None = None
    calibrated: bool = False
    model_version: str
    generated_at: datetime
    is_demo: bool = True


class Message(BaseModel):
    message_id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    kind: str
    text: str | None = None
    client_message_id: str | None = None
    assessment: Assessment | None = None
    next_steps: list[str] = Field(default_factory=list)
    created_at: datetime
    is_demo: bool = False


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=120)


class Conversation(BaseModel):
    conversation_id: str
    owner_id: str
    title: str
    created_at: datetime
    last_message_at: datetime


class SendResult(BaseModel):
    user_message: Message
    assistant_message: Message

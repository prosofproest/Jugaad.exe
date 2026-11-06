"""Request and response models for conversational capture (spec 08 §6–§8)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

AssessmentState = Literal["assessed", "abstained", "unsupported_crop", "failed"]


class ImageRef(BaseModel):
    """A reference to a server-side upload created by ``POST /v1/uploads``.

    The chat never accepts raw image bytes inside the JSON message: the client
    uploads first, then references the resulting ``upload_id``. Metadata fields
    are echoed for traceability but are not trusted for storage.
    """

    upload_id: str | None = Field(default=None, max_length=64)
    filename: str | None = Field(default=None, max_length=255)
    content_type: str | None = Field(default=None, max_length=100)
    content_hash: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def _requires_upload_id(self) -> "ImageRef":
        if not self.upload_id:
            raise ValueError("image.upload_id is required; upload the file first")
        return self


class MessageCreate(BaseModel):
    client_message_id: str = Field(min_length=1, max_length=128)
    text: str | None = Field(default=None, max_length=1000)
    image: ImageRef | None = None
    # Optional context. No default crop is invented; ``None`` means unknown.
    crop_id: str | None = Field(default=None, max_length=80)


class Candidate(BaseModel):
    label: str
    display_name: str | None = None
    score: float


class Assessment(BaseModel):
    state: AssessmentState
    reason_code: str | None = None
    reason_text: str | None = None
    quality_flag: str | None = None
    quality_flags: list[str] = Field(default_factory=list)
    candidates: list[Candidate] = Field(default_factory=list)
    confidence_band: str | None = None
    calibrated: bool = False
    model_version: str
    generated_at: datetime
    is_demo: bool = True
    observation_id: str | None = None
    error_code: str | None = None
    retryable: bool = False


class ImageRefOut(BaseModel):
    """The stored image as rendered in a message bubble."""

    upload_id: str
    filename: str
    content_type: str
    content_hash: str
    width: int
    height: int
    quality_result: str
    quality_flags: list[str] = Field(default_factory=list)
    preview_url: str


class ReviewRequestOut(BaseModel):
    review_request_id: str
    conversation_id: str
    message_id: str
    status: str
    reason: str | None = None
    submitted_at: datetime


class Message(BaseModel):
    message_id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    kind: str
    text: str | None = None
    client_message_id: str | None = None
    observation_id: str | None = None
    image: ImageRefOut | None = None
    assessment: Assessment | None = None
    review_request: ReviewRequestOut | None = None
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


class ReviewRequestCreate(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class UploadDescriptor(BaseModel):
    upload_id: str
    filename: str
    content_type: str
    content_hash: str
    size_bytes: int
    width: int
    height: int
    quality_result: str
    quality_flags: list[str] = Field(default_factory=list)
    quality_gate_version: str
    preview_url: str
    created_at: datetime
    is_demo: bool = True

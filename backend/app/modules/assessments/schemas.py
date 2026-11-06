"""Request and response models for the assessment API.

The response is the single source of truth rendered by both the chat reply and
the structured result screen (Phase 3 §6.7). Abstentions never carry a
candidate list, and no numeric score is exposed when calibration is not
approved for display.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AssessmentState = Literal["assessed", "abstained", "unsupported_crop", "failed"]


class ImageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str | None = Field(default=None, max_length=255)
    content_type: str | None = Field(default=None, max_length=100)
    content_hash: str = Field(min_length=8, max_length=128)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    laplacian_variance: float = Field(ge=0)
    mean_luma: float = Field(ge=0, le=255)
    clipped_fraction: float = Field(ge=0, le=1)
    plant_presence: float = Field(ge=0, le=1)


class AssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_assessment_id: str = Field(min_length=1, max_length=128)
    crop_id: str = Field(min_length=1, max_length=80)
    model_version: str | None = Field(default=None, max_length=120)
    image: ImageInput


class CandidateOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    display_name: str
    rank: int
    # Populated only when calibration is approved for display.
    score: float | None = None


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    assessment_id: str | None
    state: AssessmentState
    reason_code: str | None = None
    reason_text: str
    quality_flag: str | None = None
    quality_flags: list[str] = Field(default_factory=list)
    candidates: list[CandidateOut] = Field(default_factory=list)
    confidence_band: str | None = None
    calibrated: bool = False
    calibration_version: str | None = None
    model_version: str
    taxonomy_version: str | None = None
    quality_gate_version: str | None = None
    decision_thresholds: dict | None = None
    ood_score: float | None = None
    generated_at: datetime
    is_demo: bool = False
    next_steps: list[str] = Field(default_factory=list)
    not_a_diagnosis: bool = True
    supported_crops: list[str] | None = None
    error_code: str | None = None
    retryable: bool = False


class AssessmentHistory(BaseModel):
    items: list[AssessmentResponse]
    next_cursor: str | None = None

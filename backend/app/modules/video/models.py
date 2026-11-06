"""Request and response models for video reading (spec 09 §7)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

VideoState = Literal["assessed", "abstained", "failed"]


class VideoDescriptor(BaseModel):
    video_id: str
    filename: str
    content_type: str
    size_bytes: int
    duration_ms: int
    width: int
    height: int
    fps: float
    frame_count: int
    preview_url: str
    # The shipped detector is a motion heuristic, so the descriptor is demo
    # until a validated detector replaces it (D15).
    is_demo: bool = True
    created_at: datetime


class VideoFrameReading(BaseModel):
    index: int
    timestamp_ms: int
    quality_result: str
    quality_flags: list[str] = Field(default_factory=list)
    track_ids: list[int] = Field(default_factory=list)
    assessment: dict | None = None


class VideoTrackSummary(BaseModel):
    track_id: int
    frames: int
    duration_ms: int
    mean_area_fraction: float


class CandidateObserved(BaseModel):
    label: str
    display_name: str
    frames: int


class VideoReading(BaseModel):
    reading_id: str
    video_id: str
    state: VideoState
    reason_code: str | None = None
    error_code: str | None = None
    summary_text: str
    sampled_frames: int
    usable_frames: int
    duration_ms: int
    quality: dict[str, int] = Field(default_factory=dict)
    tracks: list[VideoTrackSummary] = Field(default_factory=list)
    candidates_observed: list[CandidateObserved] = Field(default_factory=list)
    frames: list[VideoFrameReading] = Field(default_factory=list)
    engine_version: str
    detector_version: str
    tracker_version: str
    is_demo: bool
    calibrated: bool = False
    confidence_band: str = "not_calibrated"
    requires_review: bool = True
    generated_at: datetime


class VideoDetail(BaseModel):
    video: VideoDescriptor
    reading: VideoReading | None = None

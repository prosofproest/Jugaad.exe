"""Video reading service (spec 09).

The pipeline is deliberately bounded and honest:

1. validate and store the clip;
2. sample a deterministic set of frames;
3. run each frame through the existing image-quality gate;
4. detect motion regions and associate them across frames;
5. run the configured assessment engine on at most ``video_assess_frames``
   usable frames;
6. render a template-only, non-diagnostic summary and persist an append-only
   reading.

The shipped detector is ``demo-motion-0.1`` and the tracker is
``bytetrack-lite-0.1``; both are labelled demo until a validated detector exists
(D15). A reading is never a diagnosis, never an area outlook and never
auto-verifies a case.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.modules.assessments.quality import QualityOutcome
from app.modules.conversations.engine import (
    AssessmentEngine,
    EngineResult,
    UploadContext,
    get_assessment_engine,
)
from app.modules.conversations.media import (
    MediaValidationError,
    inspect_image,
    resolve_stored_path,
)
from app.modules.conversations.validator import validate_reply
from app.modules.video import repository as repo
from app.modules.video.detector import MotionRegionDetector
from app.modules.video.extractor import (
    ALLOWED_VIDEO_TYPES,
    SampledFrame,
    VideoProbe,
    VideoValidationError,
    first_frame_jpeg,
    probe_video,
    sample_frames,
    sample_interval_ms,
)
from app.modules.video.models import (
    CandidateObserved,
    VideoDescriptor,
    VideoDetail,
    VideoFrameReading,
    VideoReading,
    VideoTrackSummary,
)
from app.modules.video.orm import VideoReadingRow, VideoUploadRow
from app.modules.video.summarizer import (
    SUMMARY_FAILED_TEXT,
    SUMMARY_UNSAFE_TEXT,
    VideoSummary,
    build_summary,
    failed_reason_text,
)
from app.modules.video.tracker import ByteTrackLiteTracker

NOT_A_DIAGNOSIS = "Assistive video reading — not a diagnosis."


class VideoNotFoundError(Exception):
    """Raised when a video does not exist for the caller."""


@dataclass(frozen=True)
class _FrameObservation:
    frame: SampledFrame
    quality: QualityOutcome
    track_ids: tuple[int, ...]
    sharpness: float


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _require_video(session: Session, video_id: str, owner_id: str) -> VideoUploadRow:
    row = repo.get_video(session, video_id=video_id, owner_id=owner_id)
    if row is None:
        raise VideoNotFoundError(video_id)
    return row


def _store_video(
    settings: Settings, owner_id: str, video_id: str, extension: str, data: bytes
) -> str:
    relative = f"{owner_id}/videos/{video_id}.{extension}"
    destination = Path(settings.media_root) / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return relative


def _store_frame(settings: Settings, owner_id: str, video_id: str, index: int, data: bytes) -> str:
    relative = f"{owner_id}/videos/{video_id}/frames/{index}.jpg"
    destination = Path(settings.media_root) / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return relative


def video_descriptor(row: VideoUploadRow) -> VideoDescriptor:
    return VideoDescriptor(
        video_id=row.id,
        filename=row.filename,
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        duration_ms=row.duration_ms,
        width=row.width,
        height=row.height,
        fps=row.fps,
        frame_count=row.frame_count,
        preview_url=f"/v1/videos/{row.id}/preview",
        # The detector is a motion heuristic, so the whole descriptor is demo.
        is_demo=True,
        created_at=_aware(row.created_at),
    )


def create_video_upload(
    session: Session,
    *,
    settings: Settings,
    owner_id: str,
    filename: str,
    content_type: str,
    data: bytes,
) -> VideoDescriptor:
    normalized = (content_type or "").split(";")[0].strip().lower()
    extension = ALLOWED_VIDEO_TYPES.get(normalized)
    if extension is None:
        raise VideoValidationError(
            "unsupported_media_type",
            "Only MP4, MOV and WebM videos are accepted.",
            status=415,
        )
    if not data:
        raise VideoValidationError("invalid_video", "The file is empty.")
    if len(data) > settings.video_max_bytes:
        raise VideoValidationError(
            "video_too_large",
            f"Maximum video size is {settings.video_max_bytes} bytes.",
            status=413,
        )

    video_id = _id("vid")
    storage_path = _store_video(settings, owner_id, video_id, extension, data)
    source = resolve_stored_path(settings, storage_path)
    try:
        probe = probe_video(source, settings)
    except Exception:
        # Never leave an unreadable clip on disk or a row in the database.
        source.unlink(missing_ok=True)
        raise

    row = repo.create_video(
        session,
        video_id=video_id,
        owner_id=owner_id,
        filename=(filename or "video")[:255],
        content_type=normalized,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        storage_path=storage_path,
        duration_ms=probe.duration_ms,
        width=probe.width,
        height=probe.height,
        fps=probe.fps,
        frame_count=probe.frame_count,
    )
    return video_descriptor(row)


def get_video(session: Session, video_id: str, owner_id: str) -> VideoDetail:
    row = _require_video(session, video_id, owner_id)
    reading_row = repo.latest_reading(session, video_id=video_id, owner_id=owner_id)
    return VideoDetail(
        video=video_descriptor(row),
        reading=_reading(reading_row) if reading_row is not None else None,
    )


def preview_bytes(session: Session, settings: Settings, video_id: str, owner_id: str) -> bytes:
    row = _require_video(session, video_id, owner_id)
    try:
        source = resolve_stored_path(settings, row.storage_path)
        return first_frame_jpeg(source, settings)
    except MediaValidationError as error:
        raise VideoNotFoundError(video_id) from error
    except OSError as error:
        raise VideoValidationError(
            "video_decode_failed", "The video could not be decoded.", status=415
        ) from error


def _assessment(result: EngineResult) -> dict:
    return {
        "state": result.state,
        "reason_code": result.reason_code,
        "reason_text": result.reason_text,
        "quality_flag": result.quality_flag,
        "quality_flags": list(result.quality_flags),
        "candidates": list(result.candidates),
        "confidence_band": result.confidence_band,
        "calibrated": result.calibrated,
        "model_version": result.model_version,
        "is_demo": result.is_demo,
        "error_code": result.error_code,
        "retryable": result.retryable,
    }


def _summary_payload(summary: VideoSummary) -> dict:
    return {
        "sampled_frames": summary.sampled_frames,
        "usable_frames": summary.usable_frames,
        "duration_ms": summary.duration_ms,
        "quality": summary.quality,
        "tracks": summary.tracks,
        "candidates_observed": summary.candidates_observed,
    }


def _persist_reading(
    session: Session,
    *,
    row: VideoUploadRow,
    owner_id: str,
    state: str,
    reason_code: str | None,
    error_code: str | None,
    summary_text: str,
    summary: dict | None,
    frames: list[dict] | None,
    engine_version: str,
    detector_version: str,
    tracker_version: str,
) -> VideoReadingRow:
    return repo.create_reading(
        session,
        reading_id=_id("vidr"),
        video_id=row.id,
        owner_id=owner_id,
        state=state,
        reason_code=reason_code,
        error_code=error_code,
        summary_text=summary_text,
        summary=summary,
        frames=frames,
        engine_version=engine_version,
        detector_version=detector_version,
        tracker_version=tracker_version,
        # The shipped detector is demo-only, so the reading stays demo even when
        # the assessment engine is a real provider (D15).
        is_demo=True,
        calibrated=False,
    )


def _persist_failed(
    session: Session,
    *,
    row: VideoUploadRow,
    owner_id: str,
    error_code: str,
    engine_version: str,
    detector_version: str,
    tracker_version: str,
) -> VideoReadingRow:
    return _persist_reading(
        session,
        row=row,
        owner_id=owner_id,
        state="failed",
        reason_code=error_code,
        error_code=error_code,
        summary_text=SUMMARY_FAILED_TEXT.format(reason=failed_reason_text(error_code)),
        summary=None,
        frames=None,
        engine_version=engine_version,
        detector_version=detector_version,
        tracker_version=tracker_version,
    )


def read_video(
    session: Session,
    *,
    settings: Settings,
    video_id: str,
    owner_id: str,
    engine: AssessmentEngine | None = None,
) -> VideoReading:
    row = _require_video(session, video_id, owner_id)
    engine = engine or get_assessment_engine()
    detector = MotionRegionDetector(
        threshold=settings.video_motion_threshold,
        min_area_fraction=settings.video_motion_min_area_fraction,
    )
    tracker = ByteTrackLiteTracker(
        iou_threshold=settings.video_track_iou,
        max_age=settings.video_track_max_age,
    )

    try:
        source = resolve_stored_path(settings, row.storage_path)
        probe: VideoProbe = probe_video(source, settings)
        frames = sample_frames(source, settings, probe=probe)
    except VideoValidationError as error:
        return _reading(
            _persist_failed(
                session,
                row=row,
                owner_id=owner_id,
                error_code=error.code,
                engine_version=engine.model_version,
                detector_version=detector.version,
                tracker_version=tracker.version,
            )
        )
    except (MediaValidationError, OSError, ValueError):
        return _reading(
            _persist_failed(
                session,
                row=row,
                owner_id=owner_id,
                error_code="video_decode_failed",
                engine_version=engine.model_version,
                detector_version=detector.version,
                tracker_version=tracker.version,
            )
        )

    quality_counts: dict[str, int] = {}
    observations: list[_FrameObservation] = []
    previous_gray = None
    try:
        for frame in frames:
            inspected = inspect_image(frame.jpeg, "image/jpeg")
            quality_counts[inspected.quality.result] = (
                quality_counts.get(inspected.quality.result, 0) + 1
            )
            detections = detector.detect(frame.bgr, previous_gray)
            previous_gray = detector.prepare(frame.bgr)
            matches = tracker.update(detections, frame.index)
            observations.append(
                _FrameObservation(
                    frame=frame,
                    quality=inspected.quality,
                    track_ids=tuple(sorted({track_id for track_id, _ in matches})),
                    sharpness=inspected.metrics.laplacian_variance,
                )
            )
    except (MediaValidationError, OSError, ValueError, RuntimeError):
        return _reading(
            _persist_failed(
                session,
                row=row,
                owner_id=owner_id,
                error_code="video_decode_failed",
                engine_version=engine.model_version,
                detector_version=detector.version,
                tracker_version=tracker.version,
            )
        )

    usable = [item for item in observations if item.quality.result == "pass"]
    usable.sort(key=lambda item: (-item.sharpness, item.frame.index))
    selected = sorted(
        usable[: settings.video_assess_frames],
        key=lambda item: item.frame.index,
    )

    frame_assessments: list[dict] = []
    engine_failures: list[str] = []
    for item in selected:
        storage_path = _store_frame(settings, owner_id, row.id, item.frame.index, item.frame.jpeg)
        context = UploadContext(
            upload_id=row.id,
            sha256=hashlib.sha256(item.frame.jpeg).hexdigest(),
            width=item.frame.width,
            height=item.frame.height,
            quality_result=item.quality.result,
            quality_flags=tuple(item.quality.flags),
            storage_path=storage_path,
        )
        try:
            result = engine.assess(upload=context, crop_id=None, context=None)
        except Exception:  # noqa: BLE001 - an engine crash is a failed reading
            engine_failures.append("model_unavailable")
            continue
        if result.state == "failed":
            engine_failures.append(result.error_code or "model_unavailable")
        frame_assessments.append(
            {
                "index": item.frame.index,
                "timestamp_ms": item.frame.timestamp_ms,
                "quality_result": item.quality.result,
                "quality_flags": list(item.quality.flags),
                "track_ids": list(item.track_ids),
                "assessment": _assessment(result),
            }
        )

    if selected and len(engine_failures) == len(selected):
        return _reading(
            _persist_failed(
                session,
                row=row,
                owner_id=owner_id,
                error_code=engine_failures[0],
                engine_version=engine.model_version,
                detector_version=detector.version,
                tracker_version=tracker.version,
            )
        )

    summary = build_summary(
        sampled_frames=len(frames),
        quality_counts=quality_counts,
        duration_ms=probe.duration_ms,
        frame_assessments=frame_assessments,
        tracks=tracker.tracks,
        interval_ms=sample_interval_ms(probe, settings),
        engine_version=engine.model_version,
        detector_version=detector.version,
        tracker_version=tracker.version,
        is_demo=True,
        min_usable_frames=settings.video_min_usable_frames,
        min_duration_ms=settings.video_min_duration_ms,
    )

    validation = validate_reply(
        summary.summary_text,
        *(candidate.get("display_name") for candidate in summary.candidates_observed),
    )
    if not validation.allowed:
        return _reading(
            _persist_reading(
                session,
                row=row,
                owner_id=owner_id,
                state="failed",
                reason_code="unsafe_content_blocked",
                error_code="unsafe_content_blocked",
                summary_text=SUMMARY_UNSAFE_TEXT,
                summary=None,
                frames=None,
                engine_version=engine.model_version,
                detector_version=detector.version,
                tracker_version=tracker.version,
            )
        )

    reading_row = _persist_reading(
        session,
        row=row,
        owner_id=owner_id,
        state=summary.state,
        reason_code=summary.reason_code,
        error_code=summary.error_code,
        summary_text=summary.summary_text,
        summary=_summary_payload(summary),
        frames=frame_assessments,
        engine_version=engine.model_version,
        detector_version=detector.version,
        tracker_version=tracker.version,
    )
    return _reading(reading_row)


def _reading(row: VideoReadingRow) -> VideoReading:
    summary = row.summary or {}
    return VideoReading(
        reading_id=row.id,
        video_id=row.video_id,
        state=row.state,
        reason_code=row.reason_code,
        error_code=row.error_code,
        summary_text=row.summary_text,
        sampled_frames=int(summary.get("sampled_frames", 0)),
        usable_frames=int(summary.get("usable_frames", 0)),
        duration_ms=int(summary.get("duration_ms", 0)),
        quality={str(key): int(value) for key, value in (summary.get("quality") or {}).items()},
        tracks=[VideoTrackSummary(**item) for item in summary.get("tracks") or []],
        candidates_observed=[
            CandidateObserved(**item) for item in summary.get("candidates_observed") or []
        ],
        frames=[VideoFrameReading(**item) for item in row.frames or []],
        engine_version=row.engine_version,
        detector_version=row.detector_version,
        tracker_version=row.tracker_version,
        is_demo=row.is_demo,
        calibrated=row.calibrated,
        confidence_band="not_calibrated",
        requires_review=True,
        generated_at=_aware(row.generated_at),
    )

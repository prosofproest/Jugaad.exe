"""Persistence for video reading (spec 09 §8).

Every function takes an explicit ``Session`` so the API owns the transaction
boundary. Readings are append-only: there is no update or delete helper, so a
later engine or threshold change cannot rewrite history (R7).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.video.orm import VideoReadingRow, VideoUploadRow


def utcnow() -> datetime:
    return datetime.now(UTC)


def create_video(
    session: Session,
    *,
    video_id: str,
    owner_id: str,
    filename: str,
    content_type: str,
    size_bytes: int,
    sha256: str,
    storage_path: str,
    duration_ms: int,
    width: int,
    height: int,
    fps: float,
    frame_count: int,
) -> VideoUploadRow:
    row = VideoUploadRow(
        id=video_id,
        owner_id=owner_id,
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        sha256=sha256,
        storage_path=storage_path,
        duration_ms=duration_ms,
        width=width,
        height=height,
        fps=fps,
        frame_count=frame_count,
        created_at=utcnow(),
    )
    session.add(row)
    session.flush()
    return row


def get_video(session: Session, *, video_id: str, owner_id: str) -> VideoUploadRow | None:
    return session.scalar(
        select(VideoUploadRow).where(
            VideoUploadRow.id == video_id,
            VideoUploadRow.owner_id == owner_id,
            VideoUploadRow.deleted_at.is_(None),
        )
    )


def create_reading(
    session: Session,
    *,
    reading_id: str,
    video_id: str,
    owner_id: str,
    state: str,
    reason_code: str | None,
    error_code: str | None,
    summary_text: str,
    summary: dict | None,
    frames: list | None,
    engine_version: str,
    detector_version: str,
    tracker_version: str,
    is_demo: bool,
    calibrated: bool,
) -> VideoReadingRow:
    row = VideoReadingRow(
        id=reading_id,
        video_id=video_id,
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
        is_demo=is_demo,
        calibrated=calibrated,
        generated_at=utcnow(),
    )
    session.add(row)
    session.flush()
    return row


def latest_reading(session: Session, *, video_id: str, owner_id: str) -> VideoReadingRow | None:
    return session.scalar(
        select(VideoReadingRow)
        .where(
            VideoReadingRow.video_id == video_id,
            VideoReadingRow.owner_id == owner_id,
        )
        .order_by(VideoReadingRow.generated_at.desc(), VideoReadingRow.id.desc())
        .limit(1)
    )


def count_readings(session: Session, *, video_id: str) -> int:
    return int(
        session.scalar(
            select(func.count())
            .select_from(VideoReadingRow)
            .where(VideoReadingRow.video_id == video_id)
        )
        or 0
    )

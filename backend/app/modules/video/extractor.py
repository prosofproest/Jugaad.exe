"""Bounded video decode and frame sampling (spec 09 VID-01/VID-02).

OpenCV is used only for decode. The extractor never analyses content; it returns
a deterministic, bounded set of frames so the rest of the pipeline has a fixed
amount of work. A hostile or corrupt file is rejected before any row is stored.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.core.config import Settings

ALLOWED_VIDEO_TYPES: dict[str, str] = {
    "video/mp4": "mp4",
    "video/quicktime": "mov",
    "video/webm": "webm",
}

_JPEG_QUALITY = 85


class VideoValidationError(Exception):
    """A client-safe validation failure with a stable machine code."""

    def __init__(self, code: str, message: str, *, status: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


@dataclass(frozen=True)
class VideoProbe:
    width: int
    height: int
    fps: float
    frame_count: int
    duration_ms: int


@dataclass(frozen=True)
class SampledFrame:
    """One decoded frame, already downscaled and JPEG-encoded."""

    index: int
    timestamp_ms: int
    bgr: np.ndarray
    jpeg: bytes
    width: int
    height: int


def _capture(path: Path) -> cv2.VideoCapture:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        capture.release()
        raise VideoValidationError(
            "video_decode_failed",
            "The video could not be decoded.",
            status=415,
        )
    return capture


def probe_video(path: Path, settings: Settings) -> VideoProbe:
    """Read container metadata and enforce the duration/dimension ceilings."""

    capture = _capture(path)
    try:
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    finally:
        capture.release()

    if width < 1 or height < 1:
        raise VideoValidationError(
            "video_decode_failed",
            "The video has no readable frames.",
            status=415,
        )
    if width > settings.video_max_dimension or height > settings.video_max_dimension:
        raise VideoValidationError(
            "video_too_large",
            f"Maximum video dimension is {settings.video_max_dimension} pixels.",
        )

    if not math.isfinite(fps) or fps <= 0:
        fps = 0.0
    duration_ms = round(frame_count / fps * 1000) if fps > 0 and frame_count > 0 else 0
    if duration_ms > round(settings.video_max_duration_s * 1000):
        raise VideoValidationError(
            "video_too_long",
            f"Maximum clip duration is {settings.video_max_duration_s:g} seconds.",
        )

    return VideoProbe(
        width=width,
        height=height,
        fps=fps,
        frame_count=frame_count,
        duration_ms=duration_ms,
    )


def _downscale(frame: np.ndarray, max_side: int) -> np.ndarray:
    height, width = frame.shape[:2]
    longest = max(width, height)
    if longest <= max_side:
        return frame
    scale = max_side / longest
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return cv2.resize(frame, size, interpolation=cv2.INTER_AREA)


def _encode_jpeg(frame: np.ndarray) -> bytes:
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), _JPEG_QUALITY])
    if not ok:
        raise VideoValidationError(
            "video_decode_failed",
            "A video frame could not be encoded.",
            status=415,
        )
    return buffer.tobytes()


def sampling_step(probe: VideoProbe, settings: Settings) -> int:
    """Frame stride used by the sampler; deterministic for the same probe/settings."""

    step = 1
    if probe.fps > 0:
        step = max(1, round(probe.fps / settings.video_sample_fps))
    if probe.frame_count > 0:
        step = max(step, math.ceil(probe.frame_count / settings.video_max_frames))
    return step


def sample_interval_ms(probe: VideoProbe, settings: Settings) -> int:
    """Wall-clock interval between sampled frames, used for track durations."""

    if probe.fps <= 0:
        return 1000
    return round(sampling_step(probe, settings) / probe.fps * 1000)


def iter_sampled_frames(
    path: Path,
    settings: Settings,
    *,
    probe: VideoProbe | None = None,
) -> Iterator[SampledFrame]:
    """Yield deterministic frames on a bounded schedule.

    ``video_sample_fps`` sets the target rate; ``video_max_frames`` caps the
    total and, when the clip is long, widens the step so the sample covers the
    whole clip instead of only its opening seconds.
    """

    probe = probe or probe_video(path, settings)
    step = sampling_step(probe, settings)

    capture = _capture(path)
    try:
        index = 0
        emitted = 0
        while emitted < settings.video_max_frames:
            if index % step == 0:
                ok, frame = capture.read()
                if not ok or frame is None:
                    break
                resized = _downscale(frame, settings.video_frame_max_side)
                timestamp_ms = round(index / probe.fps * 1000) if probe.fps > 0 else index * 1000
                yield SampledFrame(
                    index=index,
                    timestamp_ms=timestamp_ms,
                    bgr=resized,
                    jpeg=_encode_jpeg(resized),
                    width=int(resized.shape[1]),
                    height=int(resized.shape[0]),
                )
                emitted += 1
            elif not capture.grab():
                break
            index += 1
    finally:
        capture.release()


def sample_frames(
    path: Path,
    settings: Settings,
    *,
    probe: VideoProbe | None = None,
) -> list[SampledFrame]:
    """Materialise the sampled frames (used by tests and preview paths)."""

    return list(iter_sampled_frames(path, settings, probe=probe))


def first_frame_jpeg(path: Path, settings: Settings) -> bytes:
    """Decode and encode the first frame for the owner-scoped preview route."""

    capture = _capture(path)
    try:
        ok, frame = capture.read()
    finally:
        capture.release()
    if not ok or frame is None:
        raise VideoValidationError(
            "video_decode_failed",
            "The video has no readable frames.",
            status=415,
        )
    return _encode_jpeg(_downscale(frame, settings.video_frame_max_side))

"""Unit tests for the video pipeline seams (spec 09 VID-02/04/05/07/08)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np
from app.core.config import Settings
from app.modules.video.detector import DEMO_DETECTOR_VERSION, Detection
from app.modules.video.extractor import probe_video, sample_frames, sample_interval_ms
from app.modules.video.summarizer import build_summary
from app.modules.video.tracker import BYTETRACK_LITE_VERSION, ByteTrackLiteTracker


def _clip(path: Path, frames: int = 30, size: int = 320) -> Path:
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (size, size)
    )
    assert writer.isOpened()
    for index in range(frames):
        frame = np.full((size, size, 3), (34, 139, 34), dtype=np.uint8)
        cv2.circle(frame, (80 + index, 160), 24, (20, 200, 240), -1)
        writer.write(frame)
    writer.release()
    return path


def test_sampling_is_deterministic_and_bounded(tmp_path: Path) -> None:
    settings = Settings()
    path = _clip(tmp_path / "sample.mp4")
    probe = probe_video(path, settings)

    first = sample_frames(path, settings, probe=probe)
    second = sample_frames(path, settings, probe=probe)

    assert 0 < len(first) <= settings.video_max_frames
    assert [frame.index for frame in first] == [frame.index for frame in second]
    assert [frame.timestamp_ms for frame in first] == [frame.timestamp_ms for frame in second]
    assert [hashlib.sha256(frame.jpeg).hexdigest() for frame in first] == [
        hashlib.sha256(frame.jpeg).hexdigest() for frame in second
    ]
    assert sample_interval_ms(probe, settings) > 0


def test_tracker_keeps_one_id_across_low_score_frames() -> None:
    tracker = ByteTrackLiteTracker(iou_threshold=0.3, max_age=5)
    ids: list[int] = []
    for index in range(6):
        half = 20 + index
        detection = Detection(
            x=140 - half,
            y=140 - half,
            width=half * 2,
            height=half * 2,
            # First detection is high-confidence, the rest exercise the
            # low-score second association stage.
            score=0.9 if index == 0 else 0.4,
        )
        matches = tracker.update([detection], index)
        ids.append(matches[0][0])

    assert len(set(ids)) == 1
    assert tracker.tracks[0].hits == 6
    assert tracker.version == BYTETRACK_LITE_VERSION
    assert DEMO_DETECTOR_VERSION == "demo-motion-0.1"


def test_summary_abstains_without_a_stable_region() -> None:
    summary = build_summary(
        sampled_frames=8,
        quality_counts={"pass": 8},
        duration_ms=2000,
        frame_assessments=[],
        tracks=[],
        interval_ms=250,
        engine_version="demo-chat-0.1",
        detector_version=DEMO_DETECTOR_VERSION,
        tracker_version=BYTETRACK_LITE_VERSION,
        is_demo=True,
        min_usable_frames=3,
        min_duration_ms=500,
    )
    assert summary.state == "abstained"
    assert summary.reason_code == "no_stable_region"
    assert summary.candidates_observed == []
    assert "No video-level assessment" in summary.summary_text


def test_summary_abstains_with_no_frames() -> None:
    summary = build_summary(
        sampled_frames=0,
        quality_counts={},
        duration_ms=0,
        frame_assessments=[],
        tracks=[],
        interval_ms=1000,
        engine_version="demo-chat-0.1",
        detector_version=DEMO_DETECTOR_VERSION,
        tracker_version=BYTETRACK_LITE_VERSION,
        is_demo=True,
        min_usable_frames=3,
        min_duration_ms=500,
    )
    assert summary.state == "abstained"
    assert summary.reason_code == "no_frames"
    assert summary.candidates_observed == []

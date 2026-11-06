"""End-to-end tests for the video-reading slice (spec 09).

The clips are synthetic and generated locally with OpenCV. They are not pest
footage and no detector model is exercised: the tests prove the bounded
pipeline, the demo detector/tracker seam, abstention, fail-closed behaviour and
append-only persistence against SQLite.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import cv2
import numpy as np
import pytest
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.modules.conversations.engine import EngineResult
from app.modules.video import repository as video_repo
from app.modules.video import service
from app.modules.video.extractor import first_frame_jpeg
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

client = TestClient(app)


def _write_clip(path: Path, *, kind: str = "growing", frames: int = 60, size: int = 320) -> bytes:
    """Write a synthetic clip and return its bytes.

    ``growing`` animates one bright region so the demo motion detector and
    tracker have something deterministic to associate. ``static`` has no motion
    and ``dark`` fails the demo quality gate.
    """

    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (size, size))
    assert writer.isOpened()
    for index in range(frames):
        if kind == "dark":
            frame = np.zeros((size, size, 3), dtype=np.uint8)
        else:
            frame = np.full((size, size, 3), (34, 139, 34), dtype=np.uint8)
            for y in range(0, size, 12):
                cv2.line(frame, (0, y), (size, (y * 7) % size), (60, 160, 60), 2)
            if kind == "growing":
                half = 20 + index
                cv2.rectangle(
                    frame,
                    (140 - half, 160 - half),
                    (140 + half, 160 + half),
                    (30, 220, 240),
                    -1,
                )
        writer.write(frame)
    writer.release()
    return path.read_bytes()


@pytest.fixture()
def video_env(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    def override() -> Iterator[Session]:
        session = factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    settings = get_settings()
    previous_root = settings.media_root
    settings.media_root = str(tmp_path / "media")
    app.dependency_overrides[get_session] = override
    try:
        yield factory
    finally:
        app.dependency_overrides.pop(get_session, None)
        settings.media_root = previous_root


def _upload(data: bytes, *, content_type: str = "video/mp4") -> dict:
    response = client.post(
        "/v1/videos",
        files={"file": ("clip.mp4", data, content_type)},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_upload_and_read_tracks_a_region(video_env: sessionmaker[Session], tmp_path: Path) -> None:
    data = _write_clip(tmp_path / "growing.mp4")
    descriptor = _upload(data)
    assert descriptor["is_demo"] is True
    assert descriptor["duration_ms"] == 6000
    assert descriptor["preview_url"] == f"/v1/videos/{descriptor['video_id']}/preview"

    response = client.post(f"/v1/videos/{descriptor['video_id']}/read")
    assert response.status_code == 201, response.text
    reading = response.json()

    assert reading["state"] == "assessed"
    assert reading["sampled_frames"] > 0
    assert reading["usable_frames"] >= 3
    assert reading["quality"].get("pass") == reading["usable_frames"]
    assert reading["detector_version"] == "demo-motion-0.1"
    assert reading["tracker_version"] == "bytetrack-lite-0.1"
    assert reading["engine_version"] == "demo-chat-0.1"
    assert reading["is_demo"] is True
    assert reading["calibrated"] is False
    assert reading["confidence_band"] == "not_calibrated"
    assert reading["requires_review"] is True

    stable = [track for track in reading["tracks"] if track["frames"] >= 2]
    assert stable, reading["tracks"]
    assert len({track["track_id"] for track in stable}) == 1
    assert stable[0]["duration_ms"] > 0

    assert 1 <= len(reading["frames"]) <= 3
    for frame in reading["frames"]:
        assert frame["assessment"]["state"] == "assessed"
        assert frame["assessment"]["is_demo"] is True
        assert frame["quality_result"] == "pass"

    detail = client.get(f"/v1/videos/{descriptor['video_id']}")
    assert detail.status_code == 200
    assert detail.json()["reading"]["reading_id"] == reading["reading_id"]


def test_preview_is_the_first_sampled_frame(
    video_env: sessionmaker[Session], tmp_path: Path
) -> None:
    path = tmp_path / "preview.mp4"
    data = _write_clip(path)
    descriptor = _upload(data)
    settings = get_settings()
    expected = first_frame_jpeg(path, settings)

    response = client.get(f"/v1/videos/{descriptor['video_id']}/preview")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["cache-control"] == "private, no-store"
    assert response.content == expected


def test_readings_are_append_only(video_env: sessionmaker[Session], tmp_path: Path) -> None:
    data = _write_clip(tmp_path / "append.mp4")
    descriptor = _upload(data)
    first = client.post(f"/v1/videos/{descriptor['video_id']}/read")
    second = client.post(f"/v1/videos/{descriptor['video_id']}/read")
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["reading_id"] != second.json()["reading_id"]

    with video_env() as session:
        assert video_repo.count_readings(session, video_id=descriptor["video_id"]) == 2


def test_static_clip_abstains_with_no_stable_region(
    video_env: sessionmaker[Session], tmp_path: Path
) -> None:
    descriptor = _upload(_write_clip(tmp_path / "static.mp4", kind="static"))
    reading = client.post(f"/v1/videos/{descriptor['video_id']}/read").json()
    assert reading["state"] == "abstained"
    assert reading["reason_code"] == "no_stable_region"
    assert reading["candidates_observed"] == []
    assert reading["requires_review"] is True


def test_dark_clip_abstains_with_insufficient_usable_frames(
    video_env: sessionmaker[Session], tmp_path: Path
) -> None:
    descriptor = _upload(_write_clip(tmp_path / "dark.mp4", kind="dark"))
    reading = client.post(f"/v1/videos/{descriptor['video_id']}/read").json()
    assert reading["state"] == "abstained"
    assert reading["reason_code"] == "insufficient_usable_frames"
    assert reading["usable_frames"] == 0
    assert reading["candidates_observed"] == []


def test_unsupported_type_is_rejected(video_env: sessionmaker[Session]) -> None:
    response = client.post(
        "/v1/videos",
        files={"file": ("clip.txt", b"not a video", "text/plain")},
    )
    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_media_type"


def test_corrupt_video_is_rejected_without_a_row(
    video_env: sessionmaker[Session],
) -> None:
    response = client.post(
        "/v1/videos",
        files={"file": ("clip.mp4", b"definitely not a video", "video/mp4")},
    )
    assert response.status_code == 415
    assert response.json()["code"] == "video_decode_failed"


def test_oversized_video_is_rejected(
    video_env: sessionmaker[Session], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "video_max_bytes", 128)
    response = client.post(
        "/v1/videos",
        files={"file": ("clip.mp4", _write_clip(tmp_path / "big.mp4"), "video/mp4")},
    )
    assert response.status_code == 413
    assert response.json()["code"] == "video_too_large"


def test_dimension_ceiling_is_enforced(
    video_env: sessionmaker[Session], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "video_max_dimension", 100)
    response = client.post(
        "/v1/videos",
        files={"file": ("clip.mp4", _write_clip(tmp_path / "wide.mp4"), "video/mp4")},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "video_too_large"


def test_engine_crash_fails_closed(
    video_env: sessionmaker[Session],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class CrashingEngine:
        model_version = "crash-1"
        is_demo = True

        def assess(self, **_: object) -> EngineResult:
            raise RuntimeError("provider exploded")

    descriptor = _upload(_write_clip(tmp_path / "crash.mp4"))
    monkeypatch.setattr(service, "get_assessment_engine", lambda: CrashingEngine())
    reading = client.post(f"/v1/videos/{descriptor['video_id']}/read").json()
    assert reading["state"] == "failed"
    assert reading["error_code"] == "model_unavailable"
    assert reading["candidates_observed"] == []


def test_unsafe_summary_is_blocked(
    video_env: sessionmaker[Session],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnsafeEngine:
        model_version = "unsafe-1"
        is_demo = True

        def assess(self, **_: object) -> EngineResult:
            return EngineResult(
                state="assessed",
                reason_text="Synthetic test result.",
                model_version=self.model_version,
                is_demo=True,
                candidates=[
                    {
                        "label": "test",
                        "display_name": "Spray with pesticide now",
                        "score": 0.9,
                    }
                ],
                confidence_band="not_calibrated",
                calibrated=False,
            )

    descriptor = _upload(_write_clip(tmp_path / "unsafe.mp4"))
    monkeypatch.setattr(service, "get_assessment_engine", lambda: UnsafeEngine())
    reading = client.post(f"/v1/videos/{descriptor['video_id']}/read").json()
    assert reading["state"] == "failed"
    assert reading["error_code"] == "unsafe_content_blocked"
    assert reading["candidates_observed"] == []
    assert "withheld" in reading["summary_text"].lower()


def test_missing_video_is_404(video_env: sessionmaker[Session]) -> None:
    assert client.get("/v1/videos/vid_missing").status_code == 404
    assert client.get("/v1/videos/vid_missing/preview").status_code == 404
    assert client.post("/v1/videos/vid_missing/read").status_code == 404


def test_settings_defaults_are_bounded() -> None:
    settings = Settings()
    assert settings.video_max_bytes > 0
    assert settings.video_max_duration_s > 0
    assert settings.video_max_frames >= settings.video_assess_frames
    assert 0 < settings.video_track_iou < 1
    assert settings.video_min_usable_frames >= 1

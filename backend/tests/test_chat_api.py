"""End-to-end tests for the persisted chat slice.

These run against SQLite in a single connection so the whole turn (upload →
quality gate → demo engine → persisted messages → review request) is exercised
without a PostgreSQL server. The production schema is the Alembic revision
``0002_chat_persistence``; SQLite is only a test transport.
"""

from __future__ import annotations

import io
import json
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from app.core.config import ChatLabel, Settings, get_settings
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.modules.conversations import (
    orm,  # noqa: F401  (registers the tables)
    service,
)
from app.modules.conversations.engine import (
    EngineResult,
    OpenAICompatibleAssessmentEngine,
    get_assessment_engine,
)
from app.modules.conversations.orm import MessageEventRow
from app.modules.conversations.validator import VALIDATOR_VERSION
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

client = TestClient(app)


def _noise_image(size: int = 512) -> Image.Image:
    """A textured green image that passes the demo quality gate."""

    image = Image.new("RGB", (size, size), (34, 139, 34))
    draw = ImageDraw.Draw(image)
    for index in range(0, size, 8):
        shade = 40 + (index % 180)
        draw.line((0, index, size, (index * 7) % size), fill=(shade, 160, 60), width=2)
    return image


def _png(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _jpeg(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


@pytest.fixture()
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
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
    get_assessment_engine.cache_clear()
    app.dependency_overrides[get_session] = override

    try:
        yield factory
    finally:
        app.dependency_overrides.pop(get_session, None)
        settings.media_root = previous_root
        get_assessment_engine.cache_clear()


def _upload(client: TestClient, data: bytes, *, content_type: str = "image/png") -> dict:
    response = client.post(
        "/v1/uploads",
        files={"file": ("leaf.png", data, content_type)},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _conversation(client: TestClient) -> dict:
    response = client.post("/v1/conversations", json={"title": "Leaf check"})
    assert response.status_code == 201, response.text
    return response.json()


def _send(client: TestClient, conversation_id: str, **body) -> dict:
    payload = {"client_message_id": "cm_1", "text": "brown spots", **body}
    response = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json=payload,
        headers={"Idempotency-Key": payload["client_message_id"]},
    )
    assert response.status_code == 200, response.text
    return response.json()


class _StubEngine:
    """Engine used to prove the safety gate runs before storage."""

    def __init__(
        self,
        *,
        reason_text: str = "Possible symptom match. This is an assistive result.",
        candidates: list[dict] | None = None,
    ) -> None:
        self.model_version = "stub-chat-0.1"
        self.is_demo = False
        self._reason_text = reason_text
        self._candidates = candidates or []

    def assess(
        self,
        *,
        upload,
        crop_id: str | None = None,
        context: str | None = None,
    ) -> EngineResult:
        del upload, crop_id, context
        return EngineResult(
            state="assessed",
            reason_text=self._reason_text,
            candidates=self._candidates,
            model_version=self.model_version,
            is_demo=False,
        )


def test_upload_is_validated_stored_and_previewable(session_factory) -> None:
    data = _png(_noise_image())
    descriptor = _upload(client, data)

    assert descriptor["quality_result"] == "pass"
    assert descriptor["content_hash"]
    assert descriptor["preview_url"] == f"/v1/uploads/{descriptor['upload_id']}"
    assert descriptor["is_demo"] is True

    preview = client.get(descriptor["preview_url"])
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "image/png"
    assert preview.content == data


def test_upload_rejects_a_non_image(session_factory) -> None:
    response = client.post(
        "/v1/uploads",
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_media_type"


def test_upload_rejects_corrupt_bytes(session_factory) -> None:
    response = client.post(
        "/v1/uploads",
        files={"file": ("leaf.png", b"definitely not a png", "image/png")},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_image"


def test_dark_image_fails_the_demo_quality_gate(session_factory) -> None:
    descriptor = _upload(client, _png(Image.new("RGB", (512, 512), (3, 3, 3))))

    assert descriptor["quality_result"] == "dark"
    assert "dark" in descriptor["quality_flags"]


def test_small_image_is_low_resolution(session_factory) -> None:
    descriptor = _upload(client, _png(_noise_image(64)))

    assert descriptor["quality_result"] == "low_resolution"


def test_assessed_turn_is_persisted_and_idempotent(session_factory) -> None:
    conversation = _conversation(client)
    descriptor = _upload(client, _png(_noise_image()))

    result = _send(
        client,
        conversation["conversation_id"],
        image={"upload_id": descriptor["upload_id"]},
    )

    assistant = result["assistant_message"]
    assert assistant["assessment"]["state"] == "assessed"
    assert assistant["assessment"]["is_demo"] is True
    assert assistant["assessment"]["calibrated"] is False
    assert len(assistant["assessment"]["candidates"]) == 3
    assert assistant["assessment"]["observation_id"] == descriptor["upload_id"]
    assert assistant["next_steps"] == ["add_context", "request_review"]
    assert result["user_message"]["image"]["upload_id"] == descriptor["upload_id"]

    # A retry with the same client_message_id returns the same pair, not a copy.
    replay = _send(
        client,
        conversation["conversation_id"],
        image={"upload_id": descriptor["upload_id"]},
    )
    assert replay["user_message"]["message_id"] == result["user_message"]["message_id"]
    assert replay["assistant_message"]["message_id"] == assistant["message_id"]

    messages = client.get(f"/v1/conversations/{conversation['conversation_id']}/messages")
    assert messages.status_code == 200
    assert len(messages.json()) == 2


def test_same_image_produces_the_same_demo_candidates(session_factory) -> None:
    data = _png(_noise_image())
    first = _upload(client, data)
    second = _upload(client, data)

    assert first["content_hash"] == second["content_hash"]

    conversation = _conversation(client)
    one = _send(
        client,
        conversation["conversation_id"],
        client_message_id="cm_a",
        image={"upload_id": first["upload_id"]},
    )
    two = _send(
        client,
        conversation["conversation_id"],
        client_message_id="cm_b",
        image={"upload_id": second["upload_id"]},
    )

    assert (
        one["assistant_message"]["assessment"]["candidates"]
        == (two["assistant_message"]["assessment"]["candidates"])
    )


def test_quality_failure_abstains_with_a_retake(session_factory) -> None:
    conversation = _conversation(client)
    descriptor = _upload(client, _png(Image.new("RGB", (512, 512), (3, 3, 3))))

    result = _send(
        client,
        conversation["conversation_id"],
        image={"upload_id": descriptor["upload_id"]},
    )

    assessment = result["assistant_message"]["assessment"]
    assert assessment["state"] == "abstained"
    assert assessment["reason_code"] == "quality_gate_failed"
    assert assessment["quality_flag"] == "dark"
    assert assessment["candidates"] == []
    assert result["assistant_message"]["next_steps"] == ["retake"]
    assert "too dark" in assessment["reason_text"].lower()


def test_text_only_turn_abstains_because_there_is_no_image(session_factory) -> None:
    conversation = _conversation(client)

    result = _send(client, conversation["conversation_id"])

    assessment = result["assistant_message"]["assessment"]
    assert assessment["state"] == "abstained"
    assert assessment["reason_code"] == "no_image"
    assert result["assistant_message"]["kind"] == "abstained"


def test_unknown_upload_is_a_404(session_factory) -> None:
    conversation = _conversation(client)

    response = client.post(
        f"/v1/conversations/{conversation['conversation_id']}/messages",
        json={
            "client_message_id": "cm_missing",
            "image": {"upload_id": "up_missing"},
        },
        headers={"Idempotency-Key": "cm_missing"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "upload_not_found"


def test_review_request_is_persisted_and_idempotent(session_factory) -> None:
    conversation = _conversation(client)
    descriptor = _upload(client, _png(_noise_image()))
    result = _send(
        client,
        conversation["conversation_id"],
        image={"upload_id": descriptor["upload_id"]},
    )
    message_id = result["assistant_message"]["message_id"]

    first = client.post(
        f"/v1/conversations/{conversation['conversation_id']}/messages/{message_id}/review",
        json={"reason": "Lesion looks unusual"},
    )
    assert first.status_code == 201, first.text
    body = first.json()
    assert body["status"] == "requested"
    assert body["message_id"] == message_id

    second = client.post(
        f"/v1/conversations/{conversation['conversation_id']}/messages/{message_id}/review",
        json={"reason": "again"},
    )
    assert second.status_code == 201
    assert second.json()["review_request_id"] == body["review_request_id"]

    messages = client.get(f"/v1/conversations/{conversation['conversation_id']}/messages").json()
    assistant = next(item for item in messages if item["role"] == "assistant")
    assert assistant["review_request"]["review_request_id"] == body["review_request_id"]


def test_review_on_a_user_message_is_rejected(session_factory) -> None:
    conversation = _conversation(client)
    result = _send(client, conversation["conversation_id"])
    user_message_id = result["user_message"]["message_id"]

    response = client.post(
        f"/v1/conversations/{conversation['conversation_id']}/messages/{user_message_id}/review",
    )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_review_target"


def test_delete_hides_the_conversation(session_factory) -> None:
    conversation = _conversation(client)

    deleted = client.delete(f"/v1/conversations/{conversation['conversation_id']}")
    assert deleted.status_code == 204

    assert client.get(f"/v1/conversations/{conversation['conversation_id']}").status_code == 404
    assert client.get("/v1/conversations").json() == []


def test_jpeg_upload_is_accepted(session_factory) -> None:
    descriptor = _upload(client, _jpeg(_noise_image()), content_type="image/jpeg")

    assert descriptor["content_type"] == "image/jpeg"
    assert descriptor["filename"] == "leaf.png"


def test_unsafe_reply_is_withheld_before_storage(session_factory, monkeypatch) -> None:
    unsafe = "Spray chlorothalonil at 2 g/L every 7 days."
    monkeypatch.setattr(
        service,
        "get_assessment_engine",
        lambda: _StubEngine(reason_text=unsafe),
    )
    conversation = _conversation(client)

    result = _send(client, conversation["conversation_id"])

    assistant = result["assistant_message"]
    assessment = assistant["assessment"]
    assert assessment["state"] == "failed"
    assert assessment["reason_code"] == "unsafe_content_blocked"
    assert assessment["error_code"] == "unsafe_content_blocked"
    assert assessment["candidates"] == []
    assert assistant["kind"] == "failed"
    assert assistant["next_steps"] == ["request_review"]
    assert "chlorothalonil" not in assistant["text"].lower()
    assert "g/l" not in assistant["text"].lower()

    stored = client.get(f"/v1/conversations/{conversation['conversation_id']}/messages").json()
    assistant_row = next(item for item in stored if item["role"] == "assistant")
    assert "chlorothalonil" not in assistant_row["text"].lower()

    with session_factory() as session:
        events = session.scalars(
            select(MessageEventRow).where(MessageEventRow.message_id == assistant["message_id"])
        ).all()
    rejection = next(event for event in events if event.event_type == "validator_rejected")
    assert rejection.detail["validator_version"] == VALIDATOR_VERSION
    assert rejection.detail["categories"] == [
        "application_instruction",
        "chemical_product",
        "dosage",
    ]
    assert "chlorothalonil" not in str(rejection.detail).lower()


def test_unsafe_candidate_name_is_withheld(session_factory, monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "get_assessment_engine",
        lambda: _StubEngine(
            candidates=[
                {
                    "label": "demo_pattern_a",
                    "display_name": "Apply fungicide",
                    "score": 0.9,
                }
            ]
        ),
    )
    conversation = _conversation(client)

    result = _send(client, conversation["conversation_id"])

    assessment = result["assistant_message"]["assessment"]
    assert assessment["state"] == "failed"
    assert assessment["candidates"] == []


def test_safe_engine_reply_is_stored(session_factory, monkeypatch) -> None:
    monkeypatch.setattr(service, "get_assessment_engine", lambda: _StubEngine())
    conversation = _conversation(client)

    result = _send(client, conversation["conversation_id"])

    assessment = result["assistant_message"]["assessment"]
    assert assessment["state"] == "assessed"
    assert assessment["reason_code"] is None
    assert result["assistant_message"]["kind"] == "assessment"


def test_provider_engine_reply_is_persisted(session_factory, monkeypatch) -> None:
    """The real adapter sees the stored image and its result is persisted."""

    settings = Settings(
        _env_file=None,
        media_root=get_settings().media_root,
        chat_api_key="test-key",
        chat_model="test-vision-1",
        chat_base_url="https://provider.invalid/v1",
        chat_labels=[
            ChatLabel(
                label="demo_leaf_spot",
                display_name="Possible leaf spot (synthetic)",
            )
        ],
        chat_labels_approved=True,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        content = json.dumps(
            {
                "abstain": False,
                "candidates": [{"label": "demo_leaf_spot", "score": 0.91}],
            }
        )
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as provider_client:
        provider = OpenAICompatibleAssessmentEngine(settings, client=provider_client)
        monkeypatch.setattr(service, "get_assessment_engine", lambda: provider)

        conversation = _conversation(client)
        descriptor = _upload(client, _png(_noise_image()))
        result = _send(
            client,
            conversation["conversation_id"],
            image={"upload_id": descriptor["upload_id"]},
        )

    assessment = result["assistant_message"]["assessment"]
    assert assessment["state"] == "assessed"
    assert assessment["is_demo"] is False
    assert assessment["model_version"] == "test-vision-1"
    assert assessment["candidates"] == [
        {
            "label": "demo_leaf_spot",
            "display_name": "Possible leaf spot (synthetic)",
            "score": 0.91,
        }
    ]

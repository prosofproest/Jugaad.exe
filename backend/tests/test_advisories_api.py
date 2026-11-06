from __future__ import annotations

import pytest
from app.api.v1 import advisories as advisory_routes
from app.main import app
from app.modules.advisories.registry import AdvisoryRegistry
from app.modules.identity.dependencies import set_identity_service
from fastapi.testclient import TestClient

from tests.support_identity import bootstrap_admin, login, make_identity_service
from tests.support_notifications import MutableClock, make_draft, populate_advisory

client = TestClient(app)


@pytest.fixture(autouse=True)
def authenticated_client():
    service_instance, _sender, clock = make_identity_service()
    bootstrap_admin(service_instance)
    set_identity_service(service_instance)
    tokens = login(service_instance, clock)
    client.headers["Authorization"] = f"Bearer {tokens.access_token}"
    try:
        yield tokens
    finally:
        if "Authorization" in client.headers:
            del client.headers["Authorization"]
        set_identity_service(None)


@pytest.fixture(autouse=True)
def reset_registry():
    advisory_routes.set_advisory_registry(None)
    yield
    advisory_routes.set_advisory_registry(None)


def _published_registry() -> AdvisoryRegistry:
    registry = AdvisoryRegistry(clock=MutableClock())
    populate_advisory(registry)
    return registry


def _query(**overrides: str):
    values = {
        "crop": "crop-1",
        "target": "target-1",
        "geo": "area-1",
        "language": "en",
    }
    values.update(overrides)
    return client.get("/v1/advisories", params=values)


def test_advisory_route_is_published_as_read_only() -> None:
    schema = client.get("/openapi.json").json()

    assert "/v1/advisories" in schema["paths"]
    assert set(schema["paths"]["/v1/advisories"]) == {"get"}


def test_empty_registry_returns_a_fallback_not_generated_text() -> None:
    response = _query()

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["fallback"]["next_step"] == "request_expert_review"
    assert "no approved advisory" in body["fallback"]["message"].lower()


def test_approved_advisory_is_served_without_internal_identifiers() -> None:
    advisory_routes.set_advisory_registry(_published_registry())

    response = _query()

    assert response.status_code == 200
    body = response.json()
    assert body["fallback"] is None
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["crop_code"] == "crop-1"
    assert item["target_code"] == "target-1"
    assert item["language"] == "en"
    assert item["approver_role"] == "pathologist"
    assert item["content_hash"]
    assert "author_id" not in item
    assert "approver_id" not in item


@pytest.mark.parametrize(
    ("crop", "target", "geo", "language"),
    [
        ("other-crop", "target-1", "area-1", "en"),
        ("crop-1", "other-target", "area-1", "en"),
        ("crop-1", "target-1", "other-area", "en"),
        ("crop-1", "target-1", "area-1", "kn"),
    ],
)
def test_out_of_scope_queries_return_only_the_fallback(
    crop: str, target: str, geo: str, language: str
) -> None:
    advisory_routes.set_advisory_registry(_published_registry())

    response = _query(crop=crop, target=target, geo=geo, language=language)

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["fallback"] is not None


def test_unapproved_draft_is_never_served() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    registry.create_draft(make_draft())
    advisory_routes.set_advisory_registry(registry)

    response = _query()

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_query_parameters_are_required_and_bounded() -> None:
    assert client.get("/v1/advisories").status_code == 422
    assert _query(crop="").status_code == 422
    assert _query(language="e").status_code == 422

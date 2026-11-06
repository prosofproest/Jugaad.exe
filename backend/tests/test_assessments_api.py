from __future__ import annotations

from pathlib import Path

import pytest
from app.api.v1 import assessments as assessment_routes
from app.main import app
from fastapi.testclient import TestClient

from tests.support import FakeAdapter, make_registry, make_request, make_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_service():
    assessment_routes.set_assessment_service(None)
    yield
    assessment_routes.set_assessment_service(None)


def _payload(request) -> dict:
    return request.model_dump(mode="json")


def _headers(request) -> dict[str, str]:
    return {"Idempotency-Key": request.client_assessment_id}


def test_assessment_route_is_published_in_openapi() -> None:
    schema = client.get("/openapi.json").json()

    assert "/v1/assessments" in schema["paths"]
    assert "/v1/assessments/{prediction_id}" in schema["paths"]


def test_unconfigured_deployment_returns_a_safe_failure() -> None:
    request = make_request()

    response = client.post("/v1/assessments", json=_payload(request), headers=_headers(request))

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "failed"
    assert body["error_code"] == "triage_not_configured"
    assert body["retryable"] is False
    assert "not a diagnosis" in body["reason_text"].lower()
    assert body["candidates"] == []


def test_assessed_response_and_history_round_trip(tmp_path: Path) -> None:
    service, _ = make_service(tmp_path)
    assessment_routes.set_assessment_service(service)
    request = make_request(client_assessment_id="api-client-1", crop_id="test_crop")

    response = client.post("/v1/assessments", json=_payload(request), headers=_headers(request))

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "assessed"
    assert body["assessment_id"]
    assert body["calibrated"] is False
    assert body["confidence_band"] == "not_calibrated"
    assert all(candidate["score"] is None for candidate in body["candidates"])

    by_id = client.get(f"/v1/assessments/{body['assessment_id']}")
    assert by_id.status_code == 200
    assert by_id.json()["assessment_id"] == body["assessment_id"]

    history = client.get("/v1/assessments?limit=10")
    assert history.status_code == 200
    assert len(history.json()["items"]) == 1


def test_idempotency_key_must_match_the_client_id(tmp_path: Path) -> None:
    service, _ = make_service(tmp_path)
    assessment_routes.set_assessment_service(service)
    request = make_request(client_assessment_id="api-client-2")

    response = client.post(
        "/v1/assessments",
        json=_payload(request),
        headers={"Idempotency-Key": "different-key"},
    )

    assert response.status_code == 400


def test_quality_failure_is_returned_as_an_abstention(tmp_path: Path) -> None:
    service, _ = make_service(tmp_path)
    assessment_routes.set_assessment_service(service)
    request = make_request(client_assessment_id="api-client-3", mean_luma=5.0)

    response = client.post("/v1/assessments", json=_payload(request), headers=_headers(request))

    body = response.json()
    assert response.status_code == 200
    assert body["state"] == "abstained"
    assert body["reason_code"] == "quality_gate_failed"
    assert body["quality_flag"] == "dark"
    assert body["candidates"] == []


def test_unsupported_crop_is_returned_with_the_supported_list(tmp_path: Path) -> None:
    service, _ = make_service(tmp_path)
    assessment_routes.set_assessment_service(service)
    request = make_request(client_assessment_id="api-client-4", crop_id="unsupported")

    response = client.post("/v1/assessments", json=_payload(request), headers=_headers(request))

    body = response.json()
    assert body["state"] == "unsupported_crop"
    assert body["supported_crops"] == ["test_crop"]


def test_unknown_assessment_returns_404(tmp_path: Path) -> None:
    service, _ = make_service(tmp_path)
    assessment_routes.set_assessment_service(service)

    response = client.get("/v1/assessments/pred_missing")

    assert response.status_code == 404


def test_an_unapproved_model_is_a_safe_failure_over_http(tmp_path: Path) -> None:
    registry, _ = make_registry(tmp_path, status="trained")
    service, _ = make_service(tmp_path, registry=registry, adapter=FakeAdapter())
    assessment_routes.set_assessment_service(service)
    request = make_request(client_assessment_id="api-client-5")

    response = client.post("/v1/assessments", json=_payload(request), headers=_headers(request))

    body = response.json()
    assert response.status_code == 200
    assert body["state"] == "failed"
    assert body["error_code"] == "model_not_approved"

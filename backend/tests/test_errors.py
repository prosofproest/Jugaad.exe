"""Every failure path returns the same problem-details envelope."""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_unknown_route_returns_problem_details() -> None:
    response = client.get("/v1/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 404
    assert body["code"] == "not_found"
    assert body["type"].startswith("https://")
    assert body["request_id"]
    assert body["fields"] == []


def test_validation_error_lists_fields() -> None:
    response = client.post("/v1/conversations", json={"title": "x" * 200})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["status"] == 422
    assert body["fields"], "validation errors must name the offending field"
    assert body["fields"][0]["field"].startswith("body")


def test_error_envelope_echoes_request_id() -> None:
    response = client.get("/v1/does-not-exist", headers={"X-Request-ID": "req_test_123"})

    assert response.json()["request_id"] == "req_test_123"


def test_health_is_still_reachable_without_auth() -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/v1/health").status_code == 200

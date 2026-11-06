from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "PS-03 API"
    assert body["version"] == "0.1.0"


def test_v1_health_returns_ok() -> None:
    response = client.get("/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unknown_route_returns_404() -> None:
    response = client.get("/v1/does-not-exist")

    assert response.status_code == 404

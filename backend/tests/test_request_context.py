"""Request-id propagation for logs, errors and debugging."""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_request_id_is_minted_when_absent() -> None:
    response = client.get("/health")

    assert response.headers["X-Request-ID"]


def test_request_id_is_preserved_when_supplied() -> None:
    response = client.get("/health", headers={"X-Request-ID": "req_abc"})

    assert response.headers["X-Request-ID"] == "req_abc"


def test_each_request_gets_its_own_id() -> None:
    first = client.get("/health").headers["X-Request-ID"]
    second = client.get("/health").headers["X-Request-ID"]

    assert first != second

"""The published contract is the OpenAPI document at /v1."""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_openapi_is_published() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    assert document["info"]["title"] == "PS-03 API"
    assert document["info"]["version"] == "0.1.0"


def test_single_versioned_prefix_is_used() -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/health" in paths
    assert "/v1/health" in paths
    assert "/v1/conversations" in paths
    assert not any(path.startswith("/v2") for path in paths)


def test_two_outputs_are_not_merged_in_the_contract() -> None:
    paths = client.get("/openapi.json").json()["paths"]
    schema = client.get("/openapi.json").json()

    # Photo assessment is served as its own resource. Area outlook arrives in
    # Phase 4 as a separate resource and must never be folded into assessment
    # or chat.
    assert "/v1/assessments" in paths
    assert "/v1/forecasts" not in paths
    assert all("forecast" not in path for path in paths if "assessment" in path)

    assessment_schema = schema["components"]["schemas"]["AssessmentResponse"]
    assert "band" not in assessment_schema["properties"]
    assert "coverage" not in assessment_schema["properties"]

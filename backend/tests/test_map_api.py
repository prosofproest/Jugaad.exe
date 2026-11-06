"""HTTP contract for the separate map layers (spec 06 §7–§8).

The route must fail closed: an unconfigured deployment returns an explicit
problem, never an empty FeatureCollection that could read as "no disease".
"""

from __future__ import annotations

import pytest
from app.api.v1 import map as map_routes
from app.main import app
from app.modules.identity.dependencies import set_identity_service
from app.modules.mapping.store import MapDataStore
from fastapi.testclient import TestClient

from tests.support_identity import bootstrap_admin, login, make_identity_service
from tests.support_mapping import (
    BOUNDARY_VERSION,
    NOW,
    make_forecast,
    make_service,
    make_store,
)

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
def reset_service():
    map_routes.set_map_service(None)
    yield
    map_routes.set_map_service(None)


def _get(layer: str, **params: str):
    values = {"crop": "crop-1", "target": "target-1"}
    values.update(params)
    return client.get(f"/v1/map/layers/{layer}", params=values)


def test_unconfigured_deployment_returns_an_explicit_problem() -> None:
    response = _get("verified_reports")

    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "map_not_configured"
    assert "FeatureCollection" not in response.text


def test_layers_are_published_as_separate_read_only_routes() -> None:
    schema = client.get("/openapi.json").json()

    path = schema["paths"]["/v1/map/layers/{layer}"]
    assert set(path) == {"get"}
    layer_schema = path["get"]["parameters"]
    assert any(parameter["name"] == "layer" for parameter in layer_schema)


def test_configured_verified_layer_serves_persisted_features() -> None:
    map_routes.set_map_service(make_service())

    response = _get("verified_reports")

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert body["layer"] == "verified_reports"
    assert body["boundary_version"] == BOUNDARY_VERSION
    assert body["aggregation_level"] == "block"
    assert body["empty"] is False
    assert body["empty_message"] is None
    assert body["small_count_suppression_applied"] is True
    ids = {feature["properties"]["aggregate_id"] for feature in body["features"]}
    assert ids == {"confirmed-1", "probable-1"}


def test_merged_risk_layer_is_rejected_before_the_service() -> None:
    map_routes.set_map_service(make_service())

    response = _get("risk")

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_missing_scope_is_a_client_error_not_an_empty_map() -> None:
    map_routes.set_map_service(make_service())

    response = client.get("/v1/map/layers/verified_reports", params={"crop": "crop-1"})

    assert response.status_code == 400
    assert response.json()["code"] == "scope_required"


def test_invalid_bbox_is_rejected_with_a_typed_error() -> None:
    map_routes.set_map_service(make_service())

    response = _get("modelled_risk", bbox="10,20,10,30")

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_bbox"


def test_boundary_version_mismatch_fails_closed() -> None:
    store = make_store()
    store.add_forecast(make_forecast(forecast_id="wrong-boundary", boundary_version="bv-other"))
    map_routes.set_map_service(make_service(store=store))

    response = _get("modelled_risk")

    assert response.status_code == 503
    assert response.json()["code"] == "boundary_version_mismatch"


def test_empty_verified_layer_carries_the_absence_warning() -> None:
    map_routes.set_map_service(make_service(store=MapDataStore()))

    response = _get("verified_reports")

    assert response.status_code == 200
    body = response.json()
    assert body["empty"] is True
    assert body["features"] == []
    assert body["empty_message"] == (
        "No verified reports in this period. This does not mean the area is disease-free."
    )


def test_date_query_alias_filters_by_validity_window() -> None:
    map_routes.set_map_service(make_service())

    inside = _get("modelled_risk", date=NOW.date().isoformat())
    outside = _get("modelled_risk", date="2026-12-31")

    assert inside.status_code == 200
    assert inside.json()["empty"] is False
    assert outside.status_code == 200
    assert outside.json()["empty"] is True


def test_boundaries_layer_needs_no_crop_or_target() -> None:
    map_routes.set_map_service(make_service())

    response = client.get("/v1/map/layers/boundaries")

    assert response.status_code == 200
    body = response.json()
    assert body["layer"] == "boundaries"
    assert body["empty"] is False

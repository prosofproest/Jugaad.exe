from __future__ import annotations

from datetime import timedelta

import pytest
from app.modules.mapping.models import BBox, MapLayerResponse, MapUnavailable
from app.modules.mapping.store import MapDataStore
from pydantic import ValidationError

from tests.support_mapping import (
    NOW,
    make_forecast,
    make_policy,
    make_query,
    make_service,
    make_store,
)


def _ids(response: MapLayerResponse) -> set[str]:
    return {
        str(feature.properties.get("aggregate_id") or feature.properties.get("forecast_id"))
        for feature in response.features
    }


def test_layers_are_separate_and_carry_their_own_properties() -> None:
    service = make_service()

    verified = service.layer("verified_reports", make_query())
    unverified = service.layer("unverified_reports", make_query())
    risk = service.layer("modelled_risk", make_query())
    coverage = service.layer("coverage", make_query())
    boundaries = service.layer("boundaries", make_query())

    assert verified.layer == "verified_reports"
    assert unverified.layer == "unverified_reports"
    assert risk.layer == "modelled_risk"
    assert coverage.layer == "coverage"
    assert boundaries.layer == "boundaries"

    assert all("band" not in feature.properties for feature in verified.features)
    assert all("band" not in feature.properties for feature in unverified.features)
    assert all("verification_status" not in feature.properties for feature in risk.features)
    assert all("band" not in feature.properties for feature in coverage.features)
    assert all("band" not in feature.properties for feature in boundaries.features)


def test_verified_layer_contains_only_verified_states() -> None:
    service = make_service()

    response = service.layer("verified_reports", make_query())

    assert _ids(response) == {"confirmed-1", "probable-1"}
    assert {feature.properties["verification_status"] for feature in response.features} == {
        "confirmed",
        "probable",
    }


def test_unverified_layer_never_contains_verified_or_rejected_states() -> None:
    service = make_service()

    response = service.layer("unverified_reports", make_query())

    assert _ids(response) == {"unverified-1", "needs-visit-1"}
    assert all(
        feature.properties["verification_status"] in {"unverified", "needs_visit"}
        for feature in response.features
    )


def test_small_counts_are_suppressed_without_faking_a_zero() -> None:
    service = make_service()

    response = service.layer("verified_reports", make_query())
    by_id = {feature.properties["aggregate_id"]: feature for feature in response.features}

    visible = by_id["confirmed-1"].properties
    hidden = by_id["probable-1"].properties
    assert visible["count"] == 8
    assert visible["suppressed"] is False
    assert hidden["count"] is None
    assert hidden["suppressed"] is True
    assert response.small_count_suppression_applied is True


def test_coverage_detail_suppresses_small_counts_field_by_field() -> None:
    service = make_service()

    response = service.layer("modelled_risk", make_query())
    feature = next(
        item for item in response.features if item.properties["forecast_id"] == "scored-1"
    )

    assert feature.properties["coverage_detail"]["verified_reports_14d"] is None
    assert feature.properties["coverage_detail"]["active_reporters"] == 7
    assert feature.properties["suppressed_counts"] == ["verified_reports_14d"]


def test_insufficient_data_is_not_rendered_as_modelled_risk() -> None:
    service = make_service()

    response = service.layer("modelled_risk", make_query())

    assert _ids(response) == {"scored-1", "far-low"}
    assert all(feature.properties["band"] != "insufficient_data" for feature in response.features)


def test_probability_is_null_unless_calibration_is_approved() -> None:
    hidden = make_service().layer("modelled_risk", make_query())
    shown = make_service(policy=make_policy(probability_approved=True)).layer(
        "modelled_risk", make_query()
    )

    hidden_feature = next(
        item for item in hidden.features if item.properties["forecast_id"] == "scored-1"
    )
    shown_feature = next(
        item for item in shown.features if item.properties["forecast_id"] == "scored-1"
    )
    assert hidden_feature.properties["probability"] is None
    assert shown_feature.properties["probability"] == 0.7


def test_boundary_version_is_recorded_on_every_layer() -> None:
    service = make_service()

    for layer in [
        "verified_reports",
        "unverified_reports",
        "modelled_risk",
        "coverage",
        "boundaries",
    ]:
        response = service.layer(layer, make_query())
        assert response.boundary_version == service.policy.boundary_version


def test_boundary_version_mismatch_refuses_the_layer() -> None:
    store = make_store()
    store.add_forecast(make_forecast(forecast_id="wrong-boundary", boundary_version="bv-other"))
    service = make_service(store=store)

    with pytest.raises(MapUnavailable) as caught:
        service.layer("modelled_risk", make_query())

    assert caught.value.code == "boundary_version_mismatch"


def test_empty_verified_layer_never_implies_disease_absence() -> None:
    service = make_service(store=MapDataStore())

    response = service.layer("verified_reports", make_query())

    assert response.empty is True
    assert response.features == []
    assert response.empty_message == (
        "No verified reports in this period. This does not mean the area is disease-free."
    )


def test_bbox_filters_features_without_regenerating_geometry() -> None:
    service = make_service()

    response = service.layer("modelled_risk", make_query(bbox=BBox.parse("49,49,51,51")))

    assert _ids(response) == {"far-low"}


def test_date_filter_uses_the_persisted_validity_window() -> None:
    service = make_service()

    inside = service.layer("modelled_risk", make_query(on_date=NOW.date()))
    outside = service.layer("modelled_risk", make_query(on_date=(NOW + timedelta(days=30)).date()))

    assert inside.empty is False
    assert outside.empty is True


@pytest.mark.parametrize(
    "layer", ["verified_reports", "unverified_reports", "modelled_risk", "coverage"]
)
def test_report_risk_and_coverage_layers_require_crop_and_target(layer: str) -> None:
    service = make_service()

    with pytest.raises(MapUnavailable) as caught:
        service.layer(layer, make_query(crop=None))

    assert caught.value.code == "scope_required"


def test_boundaries_do_not_require_crop_or_target() -> None:
    service = make_service()

    response = service.layer("boundaries", make_query(crop=None, target=None))

    assert response.empty is False
    assert response.features[0].properties["boundary_version"] == service.policy.boundary_version


def test_unknown_layer_is_refused() -> None:
    service = make_service()

    with pytest.raises(MapUnavailable) as caught:
        service.layer("risk", make_query())

    assert caught.value.code == "unknown_layer"


def test_policy_rejects_overlapping_or_invalid_verified_sets() -> None:
    with pytest.raises(ValidationError):
        make_policy(
            verified_statuses=frozenset({"confirmed"}),
            unverified_statuses=frozenset({"confirmed"}),
        )

    with pytest.raises(ValidationError):
        make_policy(verified_statuses=frozenset({"rejected"}))

    with pytest.raises(ValidationError):
        make_policy(unverified_statuses=frozenset({"duplicate"}))

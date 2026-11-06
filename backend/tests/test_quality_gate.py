from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.assessments.quality import ImageMetrics, evaluate_quality

from tests.support import make_policy

POLICY = make_policy()
THRESHOLDS = POLICY.quality


def metrics(**overrides) -> ImageMetrics:
    base = {
        "width": 1200,
        "height": 900,
        "laplacian_variance": 250.0,
        "mean_luma": 128.0,
        "clipped_fraction": 0.01,
        "plant_presence": 0.9,
    }
    base.update(overrides)
    return ImageMetrics(**base)


def test_passing_image_returns_pass() -> None:
    outcome = evaluate_quality(metrics(), THRESHOLDS)

    assert outcome.result == "pass"
    assert outcome.flags == ()
    assert outcome.passed is True
    assert outcome.gate_version == "qg-synthetic-1"


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"width": 100}, "low_resolution"),
        ({"height": 100}, "low_resolution"),
        ({"mean_luma": 10.0}, "dark"),
        ({"mean_luma": 250.0}, "overexposed"),
        ({"clipped_fraction": 0.5}, "overexposed"),
        ({"laplacian_variance": 5.0}, "blurry"),
        ({"plant_presence": 0.1}, "no_plant"),
    ],
)
def test_each_quality_failure_has_a_reason_code(overrides, expected) -> None:
    outcome = evaluate_quality(metrics(**overrides), THRESHOLDS)

    assert outcome.result == expected
    assert expected in outcome.flags
    assert outcome.passed is False


def test_multiple_failures_keep_all_flags_and_a_stable_primary() -> None:
    outcome = evaluate_quality(
        metrics(width=100, laplacian_variance=1.0, plant_presence=0.0),
        THRESHOLDS,
    )

    assert outcome.result == "low_resolution"
    assert set(outcome.flags) == {"low_resolution", "blurry", "no_plant"}


def test_thresholds_are_recorded_with_the_result() -> None:
    outcome = evaluate_quality(metrics(), THRESHOLDS)

    assert outcome.thresholds["version"] == "qg-synthetic-1"
    assert outcome.thresholds["min_laplacian_variance"] == 100.0


def test_a_missing_metric_fails_closed_at_the_boundary() -> None:
    with pytest.raises(ValidationError):
        ImageMetrics.model_validate(
            {
                "width": 1200,
                "height": 900,
                "mean_luma": 128.0,
                "clipped_fraction": 0.01,
                "plant_presence": 0.9,
            }
        )

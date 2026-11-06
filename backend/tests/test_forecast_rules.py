"""Deterministic forecast rules on labelled synthetic weather.

Every value here is a synthetic test fixture. The points and thresholds are the
demo configuration in ``app.modules.forecast.rules``, not an approved operating
point or a field-validated risk model.
"""

from __future__ import annotations

import pytest
from app.modules.forecast.rules import (
    DEFAULT_THRESHOLDS,
    band_from_score,
    score_weather,
)

DRY_WEATHER = {
    "rainfall_mm_10d": 5.0,
    "consecutive_wet_days": 1,
    "relative_humidity_mean": 55.0,
    "temp_min_c": 8.0,
    "temp_max_c": 34.0,
    "leaf_wetness_hours": 2.0,
}

WET_WEATHER = {
    "rainfall_mm_10d": 62.0,
    "consecutive_wet_days": 5,
    "relative_humidity_mean": 82.0,
    "temp_min_c": 18.5,
    "temp_max_c": 27.0,
    "leaf_wetness_hours": 44.0,
}

BASELINE = {
    "rainfall_mm_10d": 0.0,
    "consecutive_wet_days": 0,
    "relative_humidity_mean": 40.0,
    "temp_min_c": 30.0,
    "temp_max_c": 35.0,
    "leaf_wetness_hours": 0.0,
}


def test_two_weather_fixtures_produce_different_scores_and_bands() -> None:
    dry = score_weather(DRY_WEATHER)
    wet = score_weather(WET_WEATHER)

    assert dry.score == 0.0
    assert dry.risk_band == "low"
    assert wet.score == 0.9
    assert wet.risk_band == "urgent"
    assert set(wet.drivers) == {
        "recent_rainfall",
        "consecutive_wet_days",
        "high_humidity",
        "temperature_window",
        "leaf_wetness",
    }
    assert wet.score > dry.score


@pytest.mark.parametrize(
    ("key", "value", "driver", "points"),
    [
        ("rainfall_mm_10d", 40.0, "recent_rainfall", 0.25),
        ("consecutive_wet_days", 4, "consecutive_wet_days", 0.2),
        ("relative_humidity_mean", 80.0, "high_humidity", 0.2),
        ("leaf_wetness_hours", 30.0, "leaf_wetness", 0.1),
    ],
)
def test_each_weather_variable_alone_changes_the_score(
    key: str, value: float, driver: str, points: float
) -> None:
    result = score_weather({**BASELINE, key: value})

    assert result.score == points
    assert result.drivers == (driver,)
    assert result.contributions[0].points == points


def test_temperature_window_requires_both_bounds() -> None:
    window = score_weather({**BASELINE, "temp_min_c": 18.0, "temp_max_c": 26.0})
    assert window.drivers == ("temperature_window",)
    assert window.score == 0.15

    # A missing bound must not be imputed as a value in the window.
    without_max = {key: value for key, value in BASELINE.items() if key != "temp_max_c"}
    without_min = {key: value for key, value in BASELINE.items() if key != "temp_min_c"}
    without_max["temp_min_c"] = 18.0
    without_min["temp_max_c"] = 26.0
    assert score_weather(without_max).score == 0.0
    assert score_weather(without_min).score == 0.0


def test_verified_reports_alone_change_the_score() -> None:
    without = score_weather(BASELINE, verified_reports_14d=0)
    with_one = score_weather(BASELINE, verified_reports_14d=1)
    with_many = score_weather(BASELINE, verified_reports_14d=7)

    assert without.score == 0.0
    assert with_one.score == with_many.score == 0.1
    assert with_one.drivers == ("verified_local_reports",)
    assert "verified_reports_14d=1 > 0" in with_one.contributions[0].detail


def test_identical_inputs_reproduce_the_same_result_and_do_not_mutate_weather() -> None:
    weather = dict(WET_WEATHER)
    before = dict(weather)

    first = score_weather(weather, verified_reports_14d=2)
    second = score_weather(weather, verified_reports_14d=2)

    assert first == second
    assert weather == before
    assert first.as_feature_dict() == second.as_feature_dict()


def test_missing_or_non_numeric_variables_are_skipped_not_defaulted() -> None:
    result = score_weather(
        {
            "rainfall_mm_10d": None,
            "consecutive_wet_days": "unknown",
            "relative_humidity_mean": True,
        }
    )

    assert result.score == 0.0
    assert result.drivers == ()
    assert result.contributions == ()


def test_band_thresholds_can_be_overridden_and_are_applied_to_the_rounded_score() -> None:
    result = score_weather(
        {**BASELINE, "rainfall_mm_10d": 40.0, "relative_humidity_mean": 80.0},
        thresholds={"moderate": 0.45, "high": 0.9, "urgent": 0.99},
    )

    assert result.score == 0.45
    assert result.risk_band == "moderate"


def test_default_threshold_boundaries_are_inclusive() -> None:
    assert band_from_score(0.0) == "low"
    assert band_from_score(DEFAULT_THRESHOLDS["moderate"]) == "moderate"
    assert band_from_score(DEFAULT_THRESHOLDS["high"]) == "high"
    assert band_from_score(DEFAULT_THRESHOLDS["urgent"]) == "urgent"

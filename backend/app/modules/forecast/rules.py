"""Deterministic area-outlook rules (ADR-004: rules baseline before ML).

This module is deliberately pure: it performs no database access, clock reads,
network calls or randomness. Given the same weather variables, verified-report
count and thresholds it returns the same score, band and drivers. The service
layer persists the result and its inputs in a feature snapshot so a forecast can
be reproduced later (Gate 4 exit criterion).

Honesty rules:

* A variable contributes only when it is present and numeric. Missing inputs are
  skipped, never defaulted to zero, so absence cannot silently become a score.
* The points, thresholds and variable names below are **demo configuration**.
  They are not an agronomist-approved operating point, not a calibrated
  probability and not validated against field data (D9 is still open).
* No score here implies disease; the output is an area-wide early outlook.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

# Demo-only band thresholds. A deployment may override them through the managed
# ``risk_band_thresholds`` configuration value (D9 approval still required).
DEFAULT_THRESHOLDS: dict[str, float] = {
    "low": 0.0,
    "moderate": 0.5,
    "high": 0.75,
    "urgent": 0.9,
}

BAND_RANK = {"insufficient_data": 0, "low": 1, "moderate": 2, "high": 3, "urgent": 4}


@dataclass(frozen=True)
class RuleContribution:
    """One explainable rule hit and the points it added."""

    driver: str
    points: float
    detail: str


@dataclass(frozen=True)
class RuleResult:
    """Deterministic result of the weather + verified-report rules."""

    score: float
    risk_band: str
    drivers: tuple[str, ...]
    contributions: tuple[RuleContribution, ...]

    def as_feature_dict(self) -> dict[str, Any]:
        """Serialisable form stored on the feature snapshot for lineage."""

        return {
            "score": self.score,
            "risk_band": self.risk_band,
            "drivers": list(self.drivers),
            "contributions": [
                {
                    "driver": item.driver,
                    "points": item.points,
                    "detail": item.detail,
                }
                for item in self.contributions
            ],
        }


def _number(variables: Mapping[str, Any], key: str) -> float | None:
    """Return a finite-ish float for a present variable, else ``None``.

    Booleans are rejected because ``True`` is not a measured weather value.
    """

    value = variables.get(key)
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def band_from_score(
    score: float,
    thresholds: Mapping[str, Any] | None = None,
) -> str:
    """Map a numeric score to a band using the configured thresholds."""

    values = thresholds or {}
    urgent = float(values.get("urgent", DEFAULT_THRESHOLDS["urgent"]))
    high = float(values.get("high", DEFAULT_THRESHOLDS["high"]))
    moderate = float(values.get("moderate", DEFAULT_THRESHOLDS["moderate"]))
    if score >= urgent:
        return "urgent"
    if score >= high:
        return "high"
    if score >= moderate:
        return "moderate"
    return "low"


def score_weather(
    weather: Mapping[str, Any] | None,
    *,
    verified_reports_14d: int = 0,
    thresholds: Mapping[str, Any] | None = None,
) -> RuleResult:
    """Score weather and verified local reports with the demo rules baseline.

    The function never mutates ``weather``. Each contribution is recorded so the
    result can be explained and re-derived from the stored feature snapshot.
    """

    variables: Mapping[str, Any] = weather or {}
    contributions: list[RuleContribution] = []

    def add(driver: str, points: float, detail: str) -> None:
        contributions.append(RuleContribution(driver=driver, points=points, detail=detail))

    rainfall = _number(variables, "rainfall_mm_10d")
    if rainfall is not None and rainfall >= 40:
        add("recent_rainfall", 0.25, f"rainfall_mm_10d={rainfall:g} >= 40")

    wet_days = _number(variables, "consecutive_wet_days")
    if wet_days is not None and wet_days >= 4:
        add("consecutive_wet_days", 0.2, f"consecutive_wet_days={wet_days:g} >= 4")

    humidity = _number(variables, "relative_humidity_mean")
    if humidity is not None and humidity >= 80:
        add("high_humidity", 0.2, f"relative_humidity_mean={humidity:g} >= 80")

    temp_min = _number(variables, "temp_min_c")
    temp_max = _number(variables, "temp_max_c")
    if temp_min is not None and temp_max is not None and 15 <= temp_min and temp_max <= 28:
        add(
            "temperature_window",
            0.15,
            f"15 <= temp_min_c={temp_min:g} and temp_max_c={temp_max:g} <= 28",
        )

    leaf_wetness = _number(variables, "leaf_wetness_hours")
    if leaf_wetness is not None and leaf_wetness >= 30:
        add("leaf_wetness", 0.1, f"leaf_wetness_hours={leaf_wetness:g} >= 30")

    reports = max(int(verified_reports_14d or 0), 0)
    if reports > 0:
        add(
            "verified_local_reports",
            0.1,
            f"verified_reports_14d={reports} > 0",
        )

    score = round(sum(item.points for item in contributions), 3)
    return RuleResult(
        score=score,
        risk_band=band_from_score(score, thresholds),
        drivers=tuple(item.driver for item in contributions),
        contributions=tuple(contributions),
    )

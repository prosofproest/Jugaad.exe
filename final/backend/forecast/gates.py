"""No-score gate for area outlooks.

The gate runs before scoring. If any condition fails, the caller persists a
forecast row with ``risk_band = insufficient_data``, a machine ``reason_code``
and the coverage detail. Values are never imputed and a failed gate never
produces a scored band.

Check order is deliberate: configuration and lineage problems are reported
before data-quality problems, so an operator sees the most actionable reason
first.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .config import ForecastConfig, TargetRules
from .domain import ReasonCode


@dataclass(frozen=True)
class GateResult:
    passed: bool
    reason_code: str
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "reason_code": self.reason_code,
            "detail": self.detail,
        }


def evaluate_gates(
    *,
    config: ForecastConfig,
    target: TargetRules,
    registry_status: str | None,
    allow_demo: bool,
    boundary_version: str,
    crop_stage: str | None,
    weather_rows: list[dict[str, Any]],
    feature_payload: dict[str, Any],
    issue_time: datetime,
    weather_age_hours: float | None,
) -> GateResult:
    """Return the first failing gate, or a pass with ``reason_code = ok``."""

    if not target.forecast_eligible:
        return GateResult(
            False,
            ReasonCode.TARGET_NOT_FORECAST_ELIGIBLE.value,
            f"{target.code} has no validated weather-driven model in v1",
        )

    if registry_status != "approved":
        return GateResult(
            False,
            ReasonCode.MODEL_NOT_APPROVED.value,
            f"registry status is {registry_status or 'missing'} for {config.model_version}",
        )
    if not config.is_servable(allow_demo=allow_demo):
        return GateResult(
            False,
            ReasonCode.MODEL_NOT_APPROVED.value,
            "demo configuration used without allow_demo",
        )

    if boundary_version != config.boundary_version:
        return GateResult(
            False,
            ReasonCode.BOUNDARY_MISMATCH.value,
            f"expected {config.boundary_version}, got {boundary_version or 'missing'}",
        )

    if not crop_stage:
        return GateResult(
            False,
            ReasonCode.CALENDAR_MISSING.value,
            "no crop stage is available at issue time",
        )

    if not weather_rows:
        return GateResult(
            False,
            ReasonCode.WEATHER_MISSING.value,
            "no weather snapshot in the lookback window",
        )

    if weather_age_hours is None:
        return GateResult(
            False,
            ReasonCode.WEATHER_MISSING.value,
            "weather lineage is missing a source timestamp",
        )

    if weather_age_hours > config.gates.weather_freshness_hours:
        return GateResult(
            False,
            ReasonCode.WEATHER_STALE.value,
            (
                f"newest weather input is {weather_age_hours:.2f}h old; "
                f"limit is {config.gates.weather_freshness_hours:.2f}h"
            ),
        )

    completeness = float(
        feature_payload.get("coverage", {}).get("weather_completeness", 0.0)
    )
    if completeness < config.gates.min_weather_completeness:
        return GateResult(
            False,
            ReasonCode.WEATHER_INCOMPLETE.value,
            (
                f"weather completeness is {completeness:.2f}; "
                f"minimum is {config.gates.min_weather_completeness:.2f}"
            ),
        )

    coverage = feature_payload.get("coverage", {})
    if (
        coverage.get("band") == "low"
        or int(coverage.get("active_reporters", 0)) < config.gates.min_active_reporters
    ):
        return GateResult(
            False,
            ReasonCode.COVERAGE_LOW.value,
            (
                f"coverage band is {coverage.get('band')} with "
                f"{coverage.get('active_reporters', 0)} active reporters; "
                f"minimum is {config.gates.min_active_reporters}"
            ),
        )

    return GateResult(True, ReasonCode.OK.value, "all gates passed")

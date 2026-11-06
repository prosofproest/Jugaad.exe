"""
Forecast gate module.
Authority: final/feature-specs/06-forecast-and-risk-map.md §3, final/feature-specs/05-data-layer.md §4.5, phase-plan.md §4.6.

Enforces strict forecast scoring pre-flight gates:
1. Weather availability & freshness (<= 24h SLA).
2. Weather completeness (all core variables present).
3. Boundary version consistency between weather and target admin unit.
4. Model registry status validation.

CRITICAL INVARIANT:
Produces explicit `risk_band = 'insufficient_data'` with `probability = None` (SQL NULL)
whenever data is missing, stale, or mismatched. NEVER silently imputes missing weather variables.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Union
from .weather_ingest import WeatherIngestRecord, CORE_WEATHER_VARIABLES


class ForecastGateResult:
    """Result of pre-flight forecast gate check."""

    def __init__(
        self,
        can_forecast: bool,
        risk_band: str,
        probability: Optional[float],
        reason_code: str,
        detail: str,
        boundary_version: str,
        weather_snapshot_id: Optional[str] = None,
        drivers: Optional[List[Dict[str, Any]]] = None,
    ):
        # Invariant check: if insufficient_data, probability must be None
        if risk_band == "insufficient_data" and probability is not None:
            raise ValueError(
                "Violation of Gate Contract: When risk_band is 'insufficient_data', probability must be None (SQL NULL)"
            )

        self.can_forecast = can_forecast
        self.risk_band = risk_band
        self.probability = probability
        self.reason_code = reason_code
        self.detail = detail
        self.boundary_version = boundary_version
        self.weather_snapshot_id = weather_snapshot_id
        self.drivers = drivers or [{"reason": reason_code, "detail": detail}]

    def to_forecast_insert_dict(
        self,
        geo_code: str,
        crop_code: str,
        target_code: str,
        valid_from: Union[datetime.date, str],
        valid_to: Union[datetime.date, str],
        model_id: str,
        is_demo: bool = True,
    ) -> Dict[str, Any]:
        """Converts refusal or gate result to forecast table row format."""
        vf = valid_from.isoformat() if isinstance(valid_from, datetime.date) else valid_from
        vt = valid_to.isoformat() if isinstance(valid_to, datetime.date) else valid_to

        return {
            "geo_code": geo_code,
            "crop_code": crop_code,
            "target_code": target_code,
            "boundary_version": self.boundary_version,
            "valid_from": vf,
            "valid_to": vt,
            "probability": self.probability,
            "risk_band": self.risk_band,
            "drivers": self.drivers,
            "model_id": model_id,
            "is_demo": is_demo,
        }


def evaluate_forecast_gate(
    weather_snapshot: Optional[Union[WeatherIngestRecord, Dict[str, Any]]],
    target_boundary_version: str,
    model_status: str = "active",
    as_of_time: Optional[datetime.datetime] = None,
    max_staleness_hours: int = 24,
) -> ForecastGateResult:
    """
    Evaluates all operational gates before running forecast models.
    Returns ForecastGateResult with either can_forecast=True or an explicit insufficient_data refusal.
    """
    as_of = as_of_time or datetime.datetime.now(datetime.timezone.utc)
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=datetime.timezone.utc)

    # Gate 1: Weather record existence
    if weather_snapshot is None:
        return ForecastGateResult(
            can_forecast=False,
            risk_band="insufficient_data",
            probability=None,
            reason_code="weather_missing",
            detail="No weather snapshot found for target geo and time window.",
            boundary_version=target_boundary_version,
            weather_snapshot_id=None,
        )

    # Convert dict to WeatherIngestRecord if needed
    if isinstance(weather_snapshot, dict):
        rec_boundary_version = weather_snapshot.get("boundary_version", "")
        rec_source_timestamp = weather_snapshot.get("source_timestamp")
        rec_variables = weather_snapshot.get("variables", {})
        rec_snapshot_id = weather_snapshot.get("id")
        rec_method = weather_snapshot.get("spatial_matching_method", "centroid_nearest_station")
    else:
        rec_boundary_version = weather_snapshot.boundary_version
        rec_source_timestamp = weather_snapshot.source_timestamp
        rec_variables = weather_snapshot.variables
        rec_snapshot_id = weather_snapshot.id
        rec_method = weather_snapshot.spatial_matching_method

    # Gate 2: Boundary version alignment
    if rec_boundary_version != target_boundary_version:
        return ForecastGateResult(
            can_forecast=False,
            risk_band="insufficient_data",
            probability=None,
            reason_code="boundary_mismatch",
            detail=(
                f"Weather boundary version '{rec_boundary_version}' does not match "
                f"forecast target boundary version '{target_boundary_version}'."
            ),
            boundary_version=target_boundary_version,
            weather_snapshot_id=rec_snapshot_id,
        )

    # Gate 3: Weather freshness (<= max_staleness_hours)
    if isinstance(rec_source_timestamp, str):
        source_dt = datetime.datetime.fromisoformat(rec_source_timestamp)
    else:
        source_dt = rec_source_timestamp

    if source_dt.tzinfo is None:
        source_dt = source_dt.replace(tzinfo=datetime.timezone.utc)

    age_hours = (as_of - source_dt).total_seconds() / 3600.0
    if age_hours > max_staleness_hours:
        return ForecastGateResult(
            can_forecast=False,
            risk_band="insufficient_data",
            probability=None,
            reason_code="weather_stale",
            detail=(
                f"Weather data age is {age_hours:.1f} hours, exceeding SLA maximum of {max_staleness_hours} hours."
            ),
            boundary_version=target_boundary_version,
            weather_snapshot_id=rec_snapshot_id,
        )

    # Gate 4: Weather variable completeness (never silently impute)
    missing_vars = [k for k in CORE_WEATHER_VARIABLES if k not in rec_variables or rec_variables[k] is None]
    if missing_vars:
        return ForecastGateResult(
            can_forecast=False,
            risk_band="insufficient_data",
            probability=None,
            reason_code="weather_incomplete",
            detail=f"Incomplete weather payload; missing core variables: {sorted(missing_vars)}. Silent imputation prohibited.",
            boundary_version=target_boundary_version,
            weather_snapshot_id=rec_snapshot_id,
        )

    # Gate 5: Model Registry Status Check
    if model_status not in ("active", "staging_approved"):
        return ForecastGateResult(
            can_forecast=False,
            risk_band="insufficient_data",
            probability=None,
            reason_code="model_inactive",
            detail=f"Model status is '{model_status}'. Scoring prohibited unless model is active or staging_approved.",
            boundary_version=target_boundary_version,
            weather_snapshot_id=rec_snapshot_id,
        )

    # All gates passed
    return ForecastGateResult(
        can_forecast=True,
        risk_band="ready_for_scoring",
        probability=0.0,  # Placeholder indicating readiness, actual score applied by model
        reason_code="sufficient",
        detail="All data sufficiency and model validation gates passed.",
        boundary_version=target_boundary_version,
        weather_snapshot_id=rec_snapshot_id,
        drivers=[{"reason": "sufficient", "spatial_matching": rec_method}],
    )


"""
Weather ingestion module.
Authority: final/feature-specs/05-data-layer.md §4.5, final/feature-specs/06-forecast-and-risk-map.md §3, phase-plan.md §4.6.

Ingests weather variables (temperature, humidity, rainfall, wet-day runs, wind, leaf-wetness proxy)
with source timestamps, freshness metadata, spatial-matching method, and boundary version.
Enforces explicit refusal (`insufficient_data`) for missing or stale records — never silent imputation.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

ALLOWED_SPATIAL_METHODS = {
    "centroid_nearest_station",
    "grid_areal_weighted_mean",
    "station_idw",
    "admin_polygon_intersection",
    "station_exact",
}

CORE_WEATHER_VARIABLES = {
    "temperature_mean_c",
    "relative_humidity_mean_pct",
    "rainfall_mm",
    "wet_day_runs",
    "wind_speed_ms",
}

# Physical bounds for sanity checks
PHYSICAL_BOUNDS: Dict[str, Tuple[float, float]] = {
    "temperature_min_c": (-10.0, 55.0),
    "temperature_max_c": (-5.0, 60.0),
    "temperature_mean_c": (-10.0, 55.0),
    "relative_humidity_min_pct": (0.0, 100.0),
    "relative_humidity_max_pct": (0.0, 100.0),
    "relative_humidity_mean_pct": (0.0, 100.0),
    "rainfall_mm": (0.0, 500.0),
    "wet_day_runs": (0, 365),
    "wind_speed_ms": (0.0, 80.0),
    "leaf_wetness_proxy_hours": (0.0, 24.0),
}


class WeatherIngestRecord:
    """Represents a validated weather snapshot ingest unit."""

    def __init__(
        self,
        geo_code: str,
        boundary_version: str,
        source: str,
        source_timestamp: datetime.datetime,
        variables: Dict[str, Any],
        grid_id: Optional[str] = None,
        station_id: Optional[str] = None,
        station_distance_km: Optional[float] = None,
        spatial_matching_method: str = "centroid_nearest_station",
        fetched_at: Optional[datetime.datetime] = None,
        is_demo: bool = True,
        snapshot_id: Optional[str] = None,
    ):
        if not geo_code:
            raise ValueError("geo_code cannot be empty")
        if not boundary_version:
            raise ValueError("boundary_version cannot be empty")
        if not source:
            raise ValueError("source cannot be empty")
        if spatial_matching_method not in ALLOWED_SPATIAL_METHODS:
            raise ValueError(
                f"Invalid spatial_matching_method: {spatial_matching_method}. "
                f"Must be one of {ALLOWED_SPATIAL_METHODS}"
            )

        # Enforce timezone awareness (UTC)
        if source_timestamp.tzinfo is None:
            source_timestamp = source_timestamp.replace(tzinfo=datetime.timezone.utc)
        self.source_timestamp = source_timestamp

        self.fetched_at = fetched_at or datetime.datetime.now(datetime.timezone.utc)
        if self.fetched_at.tzinfo is None:
            self.fetched_at = self.fetched_at.replace(tzinfo=datetime.timezone.utc)

        self.id = snapshot_id or str(uuid.uuid4())
        self.geo_code = geo_code
        self.boundary_version = boundary_version
        self.source = source
        self.grid_id = grid_id
        self.station_id = station_id
        self.station_distance_km = station_distance_km
        self.spatial_matching_method = spatial_matching_method
        self.is_demo = is_demo

        # Compute freshness
        freshness_delta = self.fetched_at - self.source_timestamp
        self.freshness_seconds = max(0, int(freshness_delta.total_seconds()))

        # Validate variables and physical bounds
        self.variables = self._validate_and_normalize_variables(variables)
        self.completeness = self._compute_completeness(self.variables)
        self.is_stale = self.freshness_seconds > (24 * 3600)  # > 24 hours SLA

    @staticmethod
    def _validate_and_normalize_variables(raw_vars: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        for key, val in raw_vars.items():
            if val is None:
                continue
            # Alias resolution
            target_key = key
            if key in ("temperature_c", "temp_mean"):
                target_key = "temperature_mean_c"
            elif key in ("relative_humidity_pct", "rh_mean"):
                target_key = "relative_humidity_mean_pct"
            elif key in ("consecutive_wet_days", "wet_hours"):
                target_key = "wet_day_runs"
            elif key == "precip_mm":
                target_key = "rainfall_mm"

            # Check physical limits if known
            if target_key in PHYSICAL_BOUNDS:
                min_b, max_b = PHYSICAL_BOUNDS[target_key]
                if not (min_b <= float(val) <= max_b):
                    raise ValueError(
                        f"Weather variable {target_key}={val} is outside plausible physical range [{min_b}, {max_b}]"
                    )

            normalized[target_key] = float(val) if isinstance(val, (int, float)) else val

        # Derive leaf-wetness proxy if missing and relative humidity + rain are present
        if "leaf_wetness_proxy_hours" not in normalized:
            if "relative_humidity_mean_pct" in normalized:
                rh = normalized["relative_humidity_mean_pct"]
                rain = normalized.get("rainfall_mm", 0.0)
                # Agronomic rule-of-thumb proxy: RH >= 90% contributes proportional wetness hours
                if rh >= 90.0:
                    proxy = 12.0 * ((rh - 90.0) / 10.0) + (4.0 if rain > 2.0 else 0.0)
                    normalized["leaf_wetness_proxy_hours"] = round(min(24.0, max(0.0, proxy)), 1)
                elif rain > 5.0:
                    normalized["leaf_wetness_proxy_hours"] = 4.0
                else:
                    normalized["leaf_wetness_proxy_hours"] = 0.0

        return normalized

    @staticmethod
    def _compute_completeness(norm_vars: Dict[str, Any]) -> float:
        present_count = sum(1 for k in CORE_WEATHER_VARIABLES if k in norm_vars and norm_vars[k] is not None)
        return round(present_count / float(len(CORE_WEATHER_VARIABLES)), 3)

    def evaluate_sufficiency(
        self,
        target_boundary_version: str,
        as_of_time: Optional[datetime.datetime] = None,
        max_staleness_hours: int = 24,
        min_completeness: float = 0.80,
    ) -> Dict[str, Any]:
        """
        Evaluates whether this snapshot is sufficient to score a forecast.
        Rejects missing, stale, boundary-mismatched or incomplete data.
        Returns explicit 'insufficient_data' diagnosis; NEVER imputes silently.
        """
        as_of = as_of_time or datetime.datetime.now(datetime.timezone.utc)
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=datetime.timezone.utc)

        age_hours = (as_of - self.source_timestamp).total_seconds() / 3600.0

        # Boundary version match check
        if self.boundary_version != target_boundary_version:
            return {
                "is_sufficient": False,
                "reason_code": "boundary_mismatch",
                "detail": (
                    f"Weather snapshot matched against boundary version '{self.boundary_version}', "
                    f"but active forecast target requires '{target_boundary_version}'."
                ),
                "snapshot_id": self.id,
                "variables": self.variables,
            }

        # Freshness check
        if self.is_stale or age_hours > max_staleness_hours:
            return {
                "is_sufficient": False,
                "reason_code": "weather_stale",
                "detail": (
                    f"Weather snapshot age is {age_hours:.1f} hours, "
                    f"exceeding max allowable freshness threshold of {max_staleness_hours} hours."
                ),
                "snapshot_id": self.id,
                "variables": self.variables,
            }

        # Completeness check
        if self.completeness < min_completeness:
            missing_vars = [k for k in CORE_WEATHER_VARIABLES if k not in self.variables]
            return {
                "is_sufficient": False,
                "reason_code": "weather_incomplete",
                "detail": (
                    f"Completeness {self.completeness:.2f} is below minimum {min_completeness:.2f}. "
                    f"Missing core variables: {missing_vars}."
                ),
                "snapshot_id": self.id,
                "variables": self.variables,
            }

        return {
            "is_sufficient": True,
            "reason_code": "sufficient",
            "detail": "Weather data passes all freshness, completeness and boundary gates.",
            "snapshot_id": self.id,
            "variables": self.variables,
        }

    def to_sql_insert_dict(self) -> Dict[str, Any]:
        """Serializes for database insert."""
        return {
            "id": self.id,
            "grid_id": self.grid_id,
            "geo_code": self.geo_code,
            "boundary_version": self.boundary_version,
            "spatial_matching_method": self.spatial_matching_method,
            "station_id": self.station_id,
            "station_distance_km": self.station_distance_km,
            "source": self.source,
            "source_timestamp": self.source_timestamp,
            "fetched_at": self.fetched_at,
            "freshness_seconds": self.freshness_seconds,
            "variables": self.variables,
            "completeness": self.completeness,
            "is_stale": self.is_stale,
            "is_demo": self.is_demo,
        }


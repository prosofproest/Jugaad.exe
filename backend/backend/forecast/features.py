"""Feature construction for the area outlook.

Two invariants are enforced here, not merely documented:

1. **No leakage.** Every input row must be timestamped at or before
   ``issue_time``. A future row raises ``FeatureLeakageError`` rather than
   being silently dropped.
2. **Verified evidence only.** Forecast pressure features count only the
   evidence tiers named in the config (``confirmed`` and ``probable`` by
   default). ``unverified``, ``needs_visit``, ``duplicate``, ``unresolved``
   and ``rejected`` are excluded.

Coverage is computed from reporting activity, weather completeness and the
verified-evidence count. It is a statement about *how much we know*, never a
statement about risk.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from ..timeutil import days_between, iso_date, parse_iso, to_iso, utcnow
from .config import ForecastConfig, TargetRules
from .domain import FeatureLeakageError, coverage_band

REQUIRED_WEATHER_VARIABLES = (
    "rainfall_mm",
    "temp_mean_c",
    "temp_min_c",
    "temp_max_c",
    "humidity_mean_pct",
)


def _row_variables(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("variables")
    if isinstance(value, dict):
        return value
    value = row.get("variables_json")
    if value:
        import json

        return json.loads(value)
    return {}


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _dedupe_days(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the latest snapshot per UTC calendar date."""

    latest: dict[date, dict[str, Any]] = {}
    for row in rows:
        stamp = parse_iso(row["source_timestamp"])
        day = stamp.date()
        current = latest.get(day)
        if current is None or stamp > parse_iso(current["source_timestamp"]):
            latest[day] = row
    return [latest[day] for day in sorted(latest)]


def _consecutive_run(days: list[date]) -> int:
    best = 0
    run = 0
    previous: date | None = None
    for day in sorted(set(days)):
        if previous is not None and day == previous + timedelta(days=1):
            run += 1
        else:
            run = 1
        best = max(best, run)
        previous = day
    return best


def _weather_summary(
    rows: list[dict[str, Any]], target: TargetRules, window_days: int
) -> dict[str, Any]:
    day_rows = _dedupe_days(rows)
    rainfall: list[float] = []
    temp_mean: list[float] = []
    temp_min: list[float] = []
    temp_max: list[float] = []
    humidity: list[float] = []
    wet_days: list[date] = []
    high_humidity_days: list[date] = []
    complete_rows = 0

    for row in day_rows:
        variables = _row_variables(row)
        day = parse_iso(row["source_timestamp"]).date()
        values = {key: _num(variables.get(key)) for key in REQUIRED_WEATHER_VARIABLES}
        if all(value is not None for value in values.values()):
            complete_rows += 1

        if values["rainfall_mm"] is not None:
            rainfall.append(values["rainfall_mm"])
        if values["temp_mean_c"] is not None:
            temp_mean.append(values["temp_mean_c"])
        if values["temp_min_c"] is not None:
            temp_min.append(values["temp_min_c"])
        if values["temp_max_c"] is not None:
            temp_max.append(values["temp_max_c"])
        if values["humidity_mean_pct"] is not None:
            humidity.append(values["humidity_mean_pct"])

        rain = values["rainfall_mm"]
        rh = values["humidity_mean_pct"]
        if (rain is not None and rain >= target.wet_day_rainfall_mm) or (
            rh is not None and rh >= target.wet_day_humidity_pct
        ):
            wet_days.append(day)
        if rh is not None and rh >= target.humidity_threshold_pct:
            high_humidity_days.append(day)

    days_observed = len(day_rows)
    mean_row_completeness = (
        sum(float(row.get("completeness", 1.0)) for row in day_rows) / days_observed
        if days_observed
        else 0.0
    )
    variable_completeness = complete_rows / days_observed if days_observed else 0.0
    day_coverage = min(days_observed / window_days, 1.0) if window_days else 0.0
    weather_completeness = round(
        min(mean_row_completeness * variable_completeness * day_coverage, 1.0), 4
    )

    return {
        "window_days": window_days,
        "days_observed": days_observed,
        "rainfall_total_mm": round(sum(rainfall), 2),
        "rainfall_days": sum(1 for value in rainfall if value > 0),
        "temp_mean_c": round(sum(temp_mean) / len(temp_mean), 2) if temp_mean else None,
        "temp_min_c": round(min(temp_min), 2) if temp_min else None,
        "temp_max_c": round(max(temp_max), 2) if temp_max else None,
        "humidity_mean_pct": (
            round(sum(humidity) / len(humidity), 2) if humidity else None
        ),
        "wet_days": len(wet_days),
        "max_consecutive_wet_days": _consecutive_run(wet_days),
        "high_humidity_days": len(high_humidity_days),
        "completeness": weather_completeness,
        "mean_row_completeness": round(mean_row_completeness, 4),
        "variable_completeness": round(variable_completeness, 4),
    }


def build_features(
    *,
    issue_time: datetime,
    crop_code: str,
    target_code: str,
    geo_code: str,
    horizon_days: int,
    config: ForecastConfig,
    target: TargetRules,
    weather_rows: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    crop_stage: str | None,
    neighbor_geos: set[str] | None = None,
    days_since_planting: int | None = None,
) -> dict[str, Any]:
    """Build the immutable feature payload for one forecast issue.

    ``weather_rows`` and ``observations`` must already be limited to roughly the
    right window by the repository; this function is the authority that rejects
    anything dated after ``issue_time``.
    """

    neighbors = neighbor_geos or set()
    window_from = issue_time - timedelta(days=horizon_days)
    coverage_from = issue_time - timedelta(
        days=config.gates.coverage_window_days
    )

    checked_weather: list[dict[str, Any]] = []
    for row in weather_rows:
        stamp = parse_iso(row["source_timestamp"])
        if stamp > issue_time:
            raise FeatureLeakageError(
                "weather snapshot is dated after the forecast issue time",
                detail=f"snapshot={row.get('id')} source_timestamp={row['source_timestamp']}",
            )
        if stamp >= window_from:
            checked_weather.append(row)

    checked_observations: list[dict[str, Any]] = []
    for row in observations:
        reported = parse_iso(row["reported_at"])
        if reported > issue_time:
            raise FeatureLeakageError(
                "observation was reported after the forecast issue time",
                detail=f"observation={row.get('id')} reported_at={row['reported_at']}",
            )
        verified_at = row.get("verified_at")
        if verified_at and parse_iso(verified_at) > issue_time:
            raise FeatureLeakageError(
                "observation was verified after the forecast issue time",
                detail=f"observation={row.get('id')} verified_at={verified_at}",
            )
        checked_observations.append(row)

    weather = _weather_summary(checked_weather, target, horizon_days)
    latest_weather = (
        max(parse_iso(row["source_timestamp"]) for row in checked_weather)
        if checked_weather
        else None
    )

    eligible_tiers = set(config.event_definition.eligible_tiers)
    in_window = [
        row
        for row in checked_observations
        if parse_iso(row["event_date"]) >= window_from
        and parse_iso(row["event_date"]) <= issue_time
    ]

    verified = [
        row
        for row in in_window
        if row["verification_status"] in eligible_tiers
        and row.get("verified_at") is not None
        and row.get("target_code") == target_code
    ]
    local_verified = [row for row in verified if row["geo_code"] == geo_code]
    nearby_verified = [row for row in verified if row["geo_code"] in neighbors]
    excluded_unverified = [
        row
        for row in in_window
        if row["target_code"] == target_code
        and row["verification_status"] not in eligible_tiers
    ]

    active_reporters = {
        row["reporter_id"]
        for row in checked_observations
        if row["crop_code"] == crop_code
        and parse_iso(row["reported_at"]) >= coverage_from
    }

    weather_completeness = float(weather["completeness"])
    min_reporters = config.gates.min_active_reporters
    reporter_component = (
        min(len(active_reporters) / min_reporters, 1.0) if min_reporters else 1.0
    )
    min_verified = config.gates.min_verified_reports
    verified_window = len(local_verified) + len(nearby_verified)
    verified_component = (
        min(verified_window / min_verified, 1.0) if min_verified else 1.0
    )
    weights = config.coverage.weights
    coverage_score = round(
        reporter_component * weights["active_reporters"]
        + weather_completeness * weights["weather_completeness"]
        + verified_component * weights["verified_reports"],
        4,
    )
    band = config.coverage.band(coverage_score)

    coverage = {
        "band": band,
        "score": coverage_score,
        "window_days": config.gates.coverage_window_days,
        "active_reporters": len(active_reporters),
        "min_active_reporters": min_reporters,
        "weather_completeness": weather_completeness,
        "min_weather_completeness": config.gates.min_weather_completeness,
        "verified_reports_local": len(local_verified),
        "verified_reports_nearby": len(nearby_verified),
        "verified_reports_window": verified_window,
        "min_verified_reports": min_verified,
        "excluded_unverified_reports": len(excluded_unverified),
        "components": {
            "active_reporters": round(reporter_component, 4),
            "weather_completeness": weather_completeness,
            "verified_reports": round(verified_component, 4),
        },
    }

    week = issue_time.isocalendar().week
    season = _season_for_month(issue_time.month)
    payload: dict[str, Any] = {
        "issue_time": to_iso(issue_time),
        "window": {
            "from": to_iso(issue_time - timedelta(days=horizon_days)),
            "to": to_iso(issue_time),
            "days": horizon_days,
        },
        "weather": weather,
        "crop": {
            "crop_code": crop_code,
            "stage": crop_stage,
            "days_since_planting": days_since_planting,
            "stage_is_susceptible": (
                crop_stage in target.susceptible_stages if crop_stage else None
            ),
        },
        "seasonal": {
            "week_of_year": week,
            "season": season,
            "month": issue_time.month,
        },
        "pressure": {
            "verified_reports_local": len(local_verified),
            "verified_reports_nearby": len(nearby_verified),
            "verified_reports_window": verified_window,
            "excluded_unverified_reports": len(excluded_unverified),
            "eligible_tiers": sorted(eligible_tiers),
        },
        "coverage": coverage,
        "scoring": config.scoring_block(target),
        "event_definition": config.event_definition.as_dict(),
        "lineage": {
            "weather_snapshot_ids": [
                row["id"] for row in checked_weather
            ],
            "observation_ids": [row["id"] for row in verified],
            "weather_sources": sorted(
                {row["source"] for row in checked_weather}
            ),
            "latest_weather_source_timestamp": (
                to_iso(latest_weather) if latest_weather else None
            ),
            "config_hash": config.config_hash,
            "boundary_version": config.boundary_version,
            "generated_at": to_iso(utcnow()),
        },
    }
    return payload


def _season_for_month(month: int) -> str:
    if 6 <= month <= 10:
        return "kharif"
    if month in (11, 12, 1, 2):
        return "rabi"
    return "summer"


def weather_age_hours(payload: dict[str, Any], issue_time: datetime) -> float | None:
    """Age of the newest weather input at issue time, in hours."""

    latest = payload.get("lineage", {}).get("latest_weather_source_timestamp")
    if not latest:
        return None
    return round(days_between(parse_iso(latest), issue_time) * 24.0, 3)

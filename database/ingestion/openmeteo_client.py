"""
Open-Meteo weather forecast client.

Fetches hourly forecast data from Open-Meteo (the customer endpoint you shared,
or the public ``api.open-meteo.com``) and converts it into
:class:`database.ingestion.weather_ingest.WeatherIngestRecord` snapshots that
flow straight into the existing forecast gate (``database.ingestion.forecast_gate``)
and the backend :class:`app.db.models.WeatherSnapshot` table.

Authority: final/feature-specs/05-data-layer.md §4.5, phase-plan.md §4.6.

The customer API you linked requires authentication (it returned HTTP 401 without
credentials). Pass your API key via ``api_key`` (sent as the ``apikey`` query
parameter) or via ``extra_headers`` if your account uses header-based auth.

Usage::

    from database.ingestion.openmeteo_client import OpenMeteoClient

    # The URL you shared (api.open-meteo.com, 7-day forecast, Asia/Kolkata):
    client = OpenMeteoClient(
        base_url="https://api.open-meteo.com/v1/forecast",
        extra_params={"utm_source": "chatgpt.com"},
    )
    records = client.fetch_and_build_records(
        latitude=12.9716,
        longitude=77.5946,
        geo_code="KA-BLR-01",          # your admin block/mandal code
        boundary_version="open-meteo-2026-v1",
        forecast_days=7,
        timezone="Asia/Kolkata",
    )
    for rec in records:
        print(rec.source_timestamp.isoformat(), rec.variables, "complete=", rec.completeness)

    # Insert into the backend WeatherSnapshot table:
    # from app.db.models import WeatherSnapshot
    # db.add(WeatherSnapshot(**snapshot_dict(rec)))   # see snapshot_dict() below
"""

from __future__ import annotations

import datetime as _dt
from collections import OrderedDict, defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence

try:  # httpx is a declared backend dependency; fall back to stdlib urllib.
    import httpx as _httpx

    _HAS_HTTPX = True
except Exception:  # pragma: no cover - fallback path
    _HAS_HTTPX = False
    import urllib.request as _urllib_request
    import urllib.error as _urllib_error

from .weather_ingest import CORE_WEATHER_VARIABLES, WeatherIngestRecord

DEFAULT_BASE_URL = "https://customer-api.open-meteo.com/v1/forecast"
DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_FORECAST_DAYS = 7
DEFAULT_REQUEST_TIMEOUT_SECONDS = 30.0

# Open-Meteo hourly variable name -> internal canonical variable name.
# The first five map to CORE_WEATHER_VARIABLES (validated + completeness-checked
# by WeatherIngestRecord / forecast gate). Everything else is stored as an extra
# descriptive variable.
OMETEO_TO_INTERNAL: Dict[str, str] = {
    "temperature_2m": "temperature_mean_c",
    "relative_humidity_2m": "relative_humidity_mean_pct",
    "dew_point_2m": "dew_point_mean_c",
    "apparent_temperature": "apparent_temperature_mean_c",
    "precipitation_probability": "precipitation_probability_mean_pct",
    "precipitation": "rainfall_mm",
    "rain": "rain_hourly_mm",
    "showers": "showers_hourly_mm",
    "wind_speed_10m": "wind_speed_ms",
    "wind_direction_10m": "wind_direction_mean_deg",
    "wind_gusts_10m": "wind_gusts_max_ms",
    "soil_moisture_0_to_1cm": "soil_moisture_0_to_1cm",
    "soil_moisture_1_to_3cm": "soil_moisture_1_to_3cm",
    "soil_moisture_3_to_9cm": "soil_moisture_3_to_9cm",
    "soil_moisture_9_to_27cm": "soil_moisture_9_to_27cm",
    "soil_moisture_27_to_81cm": "soil_moisture_27_to_81cm",
}

_MEAN = "mean"
_SUM = "sum"
_MAX = "max"
_MIN = "min"

# Aggregation applied to the hourly values of each internal variable per day.
_AGGREGATION: Dict[str, str] = {
    "temperature_mean_c": _MEAN,
    "relative_humidity_mean_pct": _MEAN,
    "dew_point_mean_c": _MEAN,
    "apparent_temperature_mean_c": _MEAN,
    "precipitation_probability_mean_pct": _MEAN,
    "rainfall_mm": _SUM,
    "rain_hourly_mm": _SUM,
    "showers_hourly_mm": _SUM,
    "wind_speed_ms": _MEAN,
    "wind_direction_mean_deg": _MEAN,
    "wind_gusts_max_ms": _MAX,
    "soil_moisture_0_to_1cm": _MEAN,
    "soil_moisture_1_to_3cm": _MEAN,
    "soil_moisture_3_to_9cm": _MEAN,
    "soil_moisture_9_to_27cm": _MEAN,
    "soil_moisture_27_to_81cm": _MEAN,
}

# A day counts as "wet" when daily accumulated rainfall reaches this threshold.
WET_DAY_THRESHOLD_MM = 1.0

# Default set of hourly variables matching the URL you shared.
DEFAULT_HOURLY_VARIABLES: Sequence[str] = (
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation_probability",
    "precipitation",
    "rain",
    "showers",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "soil_moisture_0_to_1cm",
    "soil_moisture_1_to_3cm",
    "soil_moisture_3_to_9cm",
    "soil_moisture_9_to_27cm",
    "soil_moisture_27_to_81cm",
)


class OpenMeteoError(RuntimeError):
    """Raised when the Open-Meteo request or response cannot be handled."""


class OpenMeteoClient:
    """Thin client over the Open-Meteo /v1/forecast endpoint."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        extra_params: Optional[Dict[str, str]] = None,
        timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.extra_headers = dict(extra_headers or {})
        self.extra_params = dict(extra_params or {})
        self.timeout_seconds = timeout_seconds

    # ------------------------------------------------------------------ URL
    def build_request_url(
        self,
        latitude: float,
        longitude: float,
        hourly: Optional[Sequence[str]] = None,
        timezone: str = DEFAULT_TIMEZONE,
        past_days: int = 0,
        forecast_days: int = DEFAULT_FORECAST_DAYS,
        extra_params: Optional[Dict[str, str]] = None,
    ) -> str:
        """Build the full Open-Meteo request URL (useful for logging/audit).

        Example (the URL you shared)::

            https://api.open-meteo.com/v1/forecast?latitude=12.9716&longitude=77.5946
            &hourly=temperature_2m,relative_humidity_2m,...,soil_moisture_27_to_81cm
            &forecast_days=7&timezone=Asia%2FKolkata&utm_source=chatgpt.com
        """
        hourly = list(hourly or DEFAULT_HOURLY_VARIABLES)
        params: List[str] = [
            f"latitude={latitude}",
            f"longitude={longitude}",
            f"hourly={','.join(hourly)}",
            f"timezone={timezone}",
            f"past_days={int(past_days)}",
            f"forecast_days={int(forecast_days)}",
        ]
        if self.api_key:
            params.append("apikey=" + self.api_key)
        merged_extra = dict(self.extra_params)
        merged_extra.update(extra_params or {})
        for key, value in merged_extra.items():
            params.append(f"{key}={value}")
        return self.base_url + "?" + "&".join(params)

    # ------------------------------------------------------------------ HTTP
    def _get(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        if _HAS_HTTPX:
            with _httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(url, headers=headers)
            try:
                response.raise_for_status()
            except _httpx.HTTPStatusError as exc:
                raise OpenMeteoError(
                    f"Open-Meteo request failed with HTTP {exc.response.status_code}: "
                    f"{exc.response.text[:500]}"
                ) from exc
            return response.json()  # type: ignore[no-any-return]
        # Stdlib fallback.
        req = _urllib_request.Request(url, headers=headers, method="GET")
        try:
            with _urllib_request.urlopen(req, timeout=self.timeout_seconds) as resp:  # type: ignore[attr-defined]
                body = resp.read()
        except _urllib_error.HTTPError as exc:  # type: ignore[attr-defined]
            message = exc.read().decode("utf-8", "replace")[:500]
            raise OpenMeteoError(
                f"Open-Meteo request failed with HTTP {exc.code}: {message}"
            ) from exc
        except _urllib_error.URLError as exc:  # type: ignore[attr-defined]
            raise OpenMeteoError(f"Open-Meteo request failed: {exc}") from exc
        import json

        return json.loads(body.decode("utf-8"))

    def fetch_hourly(
        self,
        latitude: float,
        longitude: float,
        hourly: Optional[Sequence[str]] = None,
        timezone: str = DEFAULT_TIMEZONE,
        past_days: int = 0,
        forecast_days: int = DEFAULT_FORECAST_DAYS,
        extra_params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Fetch the raw Open-Meteo forecast JSON."""
        headers = dict(self.extra_headers)
        return self._get(
            self.build_request_url(
                latitude=latitude,
                longitude=longitude,
                hourly=hourly,
                timezone=timezone,
                past_days=past_days,
                forecast_days=forecast_days,
                extra_params=extra_params,
            ),
            headers=headers,
        )

    # ------------------------------------------------------------------ parse
    def build_records(
        self,
        payload: Dict[str, Any],
        geo_code: str,
        source: str = "open-meteo",
        boundary_version: str = "open-meteo-forecast",
        fetched_at: Optional[_dt.datetime] = None,
        is_demo: bool = False,
        spatial_matching_method: str = "grid_areal_weighted_mean",
    ) -> List[WeatherIngestRecord]:
        """Convert an Open-Meteo payload into daily ``WeatherIngestRecord``s.

        Hourly values are aggregated to one snapshot per local calendar day.
        ``source_timestamp`` is the start of that day expressed in UTC (the API
        returns local times when ``timezone=auto``; ``utc_offset_seconds`` is
        applied to recover UTC).
        """
        if not geo_code:
            raise ValueError("geo_code cannot be empty")
        if not boundary_version:
            raise ValueError("boundary_version cannot be empty")
        if not source:
            raise ValueError("source cannot be empty")

        fetched_at = fetched_at or _dt.datetime.now(_dt.timezone.utc)
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=_dt.timezone.utc)

        hourly = payload.get("hourly", {})
        times = hourly.get("time", [])
        if not times:
            raise OpenMeteoError("Open-Meteo payload contains no hourly time series")

        utc_offset_seconds = int(payload.get("utc_offset_seconds", 0) or 0)
        offset = _dt.timedelta(seconds=utc_offset_seconds)

        # Group hourly values by local calendar day (date portion of the time
        # string, which is already in the requested timezone).
        daily: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        for index, time_str in enumerate(times):
            local_date = time_str[:10]  # "YYYY-MM-DD"
            local_naive = _dt.datetime.fromisoformat(time_str)
            utc_dt = (local_naive - offset).replace(tzinfo=_dt.timezone.utc)
            bucket = daily.setdefault(
                local_date, {"values": defaultdict(list), "utc_start": None}
            )
            if bucket["utc_start"] is None:
                bucket["utc_start"] = utc_dt.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            for variable, values in hourly.items():
                if variable == "time":
                    continue
                if index >= len(values):
                    continue
                value = values[index]
                if value is None:
                    continue
                bucket["values"][variable].append(float(value))

        records: List[WeatherIngestRecord] = []
        wet_run = 0  # consecutive wet-day counter across the ordered days

        for local_date in sorted(daily.keys()):
            bucket = daily[local_date]
            raw_values = bucket["values"]
            source_timestamp = bucket["utc_start"]

            internal_vars: Dict[str, Any] = {}
            for om_variable, values in raw_values.items():
                if not values:
                    continue
                internal_name = OMETEO_TO_INTERNAL.get(om_variable, om_variable)
                aggregation = _AGGREGATION.get(internal_name, _MEAN)
                if aggregation == _SUM:
                    aggregated = sum(values)
                elif aggregation == _MAX:
                    aggregated = max(values)
                elif aggregation == _MIN:
                    aggregated = min(values)
                else:
                    aggregated = sum(values) / float(len(values))
                internal_vars[internal_name] = round(aggregated, 4)

            # wet_day_runs: consecutive wet days ending on this day.
            rainfall = internal_vars.get("rainfall_mm", 0.0) or 0.0
            wet_run = wet_run + 1 if rainfall >= WET_DAY_THRESHOLD_MM else 0
            internal_vars["wet_day_runs"] = float(wet_run)

            # Make sure every core variable is present (missing -> None so the
            # completeness score honestly reflects gaps; never silently imputed).
            for core in CORE_WEATHER_VARIABLES:
                internal_vars.setdefault(core, None)

            records.append(
                WeatherIngestRecord(
                    geo_code=geo_code,
                    boundary_version=boundary_version,
                    source=source,
                    source_timestamp=source_timestamp,
                    variables=internal_vars,
                    grid_id=None,
                    station_id=None,
                    station_distance_km=None,
                    spatial_matching_method=spatial_matching_method,
                    fetched_at=fetched_at,
                    is_demo=is_demo,
                )
            )

        return records

    # ------------------------------------------------------------------ high level
    def fetch_and_build_records(
        self,
        latitude: float,
        longitude: float,
        geo_code: str,
        *,
        source: str = "open-meteo",
        boundary_version: str = "open-meteo-forecast",
        hourly: Optional[Sequence[str]] = None,
        timezone: str = DEFAULT_TIMEZONE,
        past_days: int = 0,
        forecast_days: int = DEFAULT_FORECAST_DAYS,
        fetched_at: Optional[_dt.datetime] = None,
        is_demo: bool = False,
        spatial_matching_method: str = "grid_areal_weighted_mean",
        extra_params: Optional[Dict[str, str]] = None,
    ) -> List[WeatherIngestRecord]:
        """One-shot: fetch the forecast and build ingestion records."""
        payload = self.fetch_hourly(
            latitude=latitude,
            longitude=longitude,
            hourly=hourly,
            timezone=timezone,
            past_days=past_days,
            forecast_days=forecast_days,
            extra_params=extra_params,
        )
        return self.build_records(
            payload=payload,
            geo_code=geo_code,
            source=source,
            boundary_version=boundary_version,
            fetched_at=fetched_at,
            is_demo=is_demo,
            spatial_matching_method=spatial_matching_method,
        )


def snapshot_dict(record: WeatherIngestRecord) -> Dict[str, Any]:
    """Return the subset of fields that map to the backend ``WeatherSnapshot``
    ORM model (``app.db.models.WeatherSnapshot``), ready for
    ``db.add(WeatherSnapshot(**snapshot_dict(rec)))``."""
    d = record.to_sql_insert_dict()
    return {
        "id": d["id"],
        "geo_code": d["geo_code"],
        "source": d["source"],
        "source_timestamp": d["source_timestamp"],
        "fetched_at": d["fetched_at"],
        "variables": d["variables"],
        "completeness": d["completeness"],
        "is_stale": d["is_stale"],
        "is_demo": d["is_demo"],
    }


__all__ = [
    "OpenMeteoClient",
    "OpenMeteoError",
    "snapshot_dict",
    "DEFAULT_BASE_URL",
    "DEFAULT_HOURLY_VARIABLES",
    "OMETEO_TO_INTERNAL",
    "WET_DAY_THRESHOLD_MM",
]

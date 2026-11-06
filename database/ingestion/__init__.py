"""
Database ingestion package.
Authority: final/feature-specs/05-data-layer.md, final/feature-specs/06-forecast-and-risk-map.md, phase-plan.md §4.6.
"""

from .boundary_loader import BoundaryRecord
from .forecast_gate import ForecastGateResult, evaluate_forecast_gate
from .historical_ingest import HistoricalOccurrenceRecord
from .openmeteo_client import (
    DEFAULT_BASE_URL,
    DEFAULT_HOURLY_VARIABLES,
    OMETEO_TO_INTERNAL,
    OpenMeteoClient,
    OpenMeteoError,
    WET_DAY_THRESHOLD_MM,
    snapshot_dict,
)
from .weather_ingest import (
    ALLOWED_SPATIAL_METHODS,
    CORE_WEATHER_VARIABLES,
    PHYSICAL_BOUNDS,
    WeatherIngestRecord,
)

__all__ = [
    "BoundaryRecord",
    "HistoricalOccurrenceRecord",
    "WeatherIngestRecord",
    "ForecastGateResult",
    "evaluate_forecast_gate",
    "OpenMeteoClient",
    "OpenMeteoError",
    "snapshot_dict",
    "ALLOWED_SPATIAL_METHODS",
    "CORE_WEATHER_VARIABLES",
    "PHYSICAL_BOUNDS",
    "DEFAULT_BASE_URL",
    "DEFAULT_HOURLY_VARIABLES",
    "OMETEO_TO_INTERNAL",
    "WET_DAY_THRESHOLD_MM",
]


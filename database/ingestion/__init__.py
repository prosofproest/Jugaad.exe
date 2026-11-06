"""
Database ingestion package.
Authority: final/feature-specs/05-data-layer.md, final/feature-specs/06-forecast-and-risk-map.md, phase-plan.md §4.6.
"""

from .boundary_loader import BoundaryRecord
from .forecast_gate import ForecastGateResult, evaluate_forecast_gate
from .historical_ingest import HistoricalOccurrenceRecord
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
    "ALLOWED_SPATIAL_METHODS",
    "CORE_WEATHER_VARIABLES",
    "PHYSICAL_BOUNDS",
]


"""In-memory map repository.

The production repository will read persisted report aggregates, forecasts,
coverage rows and versioned boundaries. This store exists so the layer contract
can be tested without a database or real geometry.
"""

from __future__ import annotations

from app.modules.mapping.models import (
    BoundaryFeature,
    CoverageArea,
    ForecastArea,
    ReportAggregate,
)


class MapDataStore:
    def __init__(self) -> None:
        self._reports: list[ReportAggregate] = []
        self._forecasts: list[ForecastArea] = []
        self._coverage: list[CoverageArea] = []
        self._boundaries: list[BoundaryFeature] = []

    def add_report(self, report: ReportAggregate) -> None:
        self._reports.append(report)

    def add_forecast(self, forecast: ForecastArea) -> None:
        self._forecasts.append(forecast)

    def add_coverage(self, coverage: CoverageArea) -> None:
        self._coverage.append(coverage)

    def add_boundary(self, boundary: BoundaryFeature) -> None:
        self._boundaries.append(boundary)

    def reports(self) -> tuple[ReportAggregate, ...]:
        return tuple(self._reports)

    def forecasts(self) -> tuple[ForecastArea, ...]:
        return tuple(self._forecasts)

    def coverage(self) -> tuple[CoverageArea, ...]:
        return tuple(self._coverage)

    def boundaries(self) -> tuple[BoundaryFeature, ...]:
        return tuple(self._boundaries)

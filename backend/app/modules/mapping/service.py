"""Serve separate map layers from persisted aggregates (spec 06 §7–§8).

Layer separation is structural: each public method reads one collection and
emits one property shape. There is no method that reads reports and forecasts
together, so a merged "risk" feature cannot be produced here.

The service refuses to serve when the configured boundary version does not
match the stored features. It never repairs, snaps or regenerates geometry.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import UTC, datetime, time
from typing import Any

from app.modules.mapping.models import (
    BBox,
    CoverageArea,
    ForecastArea,
    Geometry,
    MapFeature,
    MapLayerResponse,
    MapPolicy,
    MapQuery,
    MapUnavailable,
    ReportAggregate,
)
from app.modules.mapping.store import MapDataStore

Clock = Callable[[], datetime]

_EMPTY_MESSAGES: dict[str, str] = {
    "verified_reports": (
        "No verified reports in this period. This does not mean the area is disease-free."
    ),
    "unverified_reports": "No unverified reports in this period.",
    "modelled_risk": "No scored outlook is available for this area and period.",
    "coverage": "No coverage data is available for this area and period.",
    "boundaries": "No boundary reference is available for this area.",
}


def _iter_numbers(value: Any) -> Iterable[float]:
    if isinstance(value, (int, float)):
        yield float(value)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_numbers(item)


def _bounds(geometry: Geometry) -> tuple[float, float, float, float]:
    numbers = list(_iter_numbers(geometry.model_dump(mode="json")["coordinates"]))
    xs = numbers[0::2]
    ys = numbers[1::2]
    if not xs or not ys:
        raise MapUnavailable("invalid_geometry")
    return min(xs), min(ys), max(xs), max(ys)


def _intersects(geometry: Geometry, bbox: BBox) -> bool:
    min_lon, min_lat, max_lon, max_lat = _bounds(geometry)
    return not (
        max_lon < bbox.min_lon
        or min_lon > bbox.max_lon
        or max_lat < bbox.min_lat
        or min_lat > bbox.max_lat
    )


class MapService:
    def __init__(
        self,
        *,
        store: MapDataStore,
        policy: MapPolicy,
        clock: Clock | None = None,
    ) -> None:
        self._store = store
        self._policy = policy
        self._clock = clock if clock is not None else (lambda: datetime.now(UTC))

    @property
    def policy(self) -> MapPolicy:
        return self._policy

    def layer(self, layer: str, query: MapQuery) -> MapLayerResponse:
        if layer == "verified_reports":
            features, suppressed = self._reports_for("verified_reports", query)
        elif layer == "unverified_reports":
            features, suppressed = self._reports_for("unverified_reports", query)
        elif layer == "modelled_risk":
            features, suppressed = self._risk(query)
        elif layer == "coverage":
            features, suppressed = self._coverage(query)
        elif layer == "boundaries":
            features, suppressed = self._boundaries(query)
        else:
            raise MapUnavailable("unknown_layer")
        return MapLayerResponse(
            layer=layer,  # type: ignore[arg-type]
            boundary_version=self._policy.boundary_version,
            generated_at=self._clock(),
            aggregation_level=self._policy.aggregation_level,
            features=features,
            empty=not features,
            empty_message=None if features else _EMPTY_MESSAGES[layer],
            small_count_suppression_applied=suppressed,
        )

    # ------------------------------------------------------------- reports

    def _reports_for(self, layer: str, query: MapQuery) -> tuple[list[MapFeature], bool]:
        self._require_scope(query)
        statuses = (
            self._policy.verified_statuses
            if layer == "verified_reports"
            else self._policy.unverified_statuses
        )
        features: list[MapFeature] = []
        suppressed_any = False
        for report in self._store.reports():
            if report.verification_status not in statuses:
                continue
            if not self._matches(report, query):
                continue
            count, suppressed = self._suppress_count(report.count)
            suppressed_any = suppressed_any or suppressed
            features.append(
                MapFeature(
                    geometry=report.geometry,
                    properties={
                        "aggregate_id": report.aggregate_id,
                        "geo_code": report.geo_code,
                        "verification_status": report.verification_status,
                        "count": count,
                        "suppressed": suppressed,
                        "crop_code": report.crop_code,
                        "target_code": report.target_code,
                        "window_from": report.window_from.isoformat(),
                        "window_to": report.window_to.isoformat(),
                        "observed_at": report.observed_at.isoformat(),
                        "is_demo": report.is_demo,
                    },
                )
            )
        return features, suppressed_any

    # ---------------------------------------------------------- modelled risk

    def _risk(self, query: MapQuery) -> tuple[list[MapFeature], bool]:
        self._require_scope(query)
        features: list[MapFeature] = []
        suppressed_any = False
        for forecast in self._store.forecasts():
            if forecast.band == "insufficient_data":
                continue
            if not self._matches(forecast, query):
                continue
            self._require_boundary_version(forecast.boundary_version)
            detail, suppressed = self._suppress_detail(forecast.coverage_detail)
            suppressed_any = suppressed_any or suppressed
            probability = forecast.probability if self._policy.probability_approved else None
            features.append(
                MapFeature(
                    geometry=forecast.geometry,
                    properties={
                        "forecast_id": forecast.forecast_id,
                        "geo_code": forecast.geo_code,
                        "crop_code": forecast.crop_code,
                        "target_code": forecast.target_code,
                        "band": forecast.band,
                        "probability": probability,
                        "coverage": forecast.coverage,
                        "coverage_detail": detail,
                        "suppressed_counts": [
                            key for key, value in detail.items() if value is None
                        ],
                        "drivers": list(forecast.drivers),
                        "model_version": forecast.model_version,
                        "issue_time": forecast.issue_time.isoformat(),
                        "valid_from": forecast.valid_from.isoformat(),
                        "valid_to": forecast.valid_to.isoformat(),
                        "is_stale": forecast.is_stale,
                        "is_demo": forecast.is_demo,
                    },
                )
            )
        return features, suppressed_any

    # -------------------------------------------------------------- coverage

    def _coverage(self, query: MapQuery) -> tuple[list[MapFeature], bool]:
        self._require_scope(query)
        features: list[MapFeature] = []
        suppressed_any = False
        for area in self._store.coverage():
            if not self._matches(area, query):
                continue
            self._require_boundary_version(area.boundary_version)
            detail, suppressed = self._suppress_detail(area.coverage_detail)
            suppressed_any = suppressed_any or suppressed
            features.append(
                MapFeature(
                    geometry=area.geometry,
                    properties={
                        "geo_code": area.geo_code,
                        "crop_code": area.crop_code,
                        "target_code": area.target_code,
                        "coverage": area.coverage,
                        "coverage_detail": detail,
                        "suppressed_counts": [
                            key for key, value in detail.items() if value is None
                        ],
                        "valid_from": area.valid_from.isoformat(),
                        "valid_to": area.valid_to.isoformat(),
                        "computed_at": area.computed_at.isoformat(),
                    },
                )
            )
        return features, suppressed_any

    # ------------------------------------------------------------ boundaries

    def _boundaries(self, query: MapQuery) -> tuple[list[MapFeature], bool]:
        features: list[MapFeature] = []
        for boundary in self._store.boundaries():
            if query.bbox is not None and not _intersects(boundary.geometry, query.bbox):
                continue
            self._require_boundary_version(boundary.boundary_version)
            features.append(
                MapFeature(
                    geometry=boundary.geometry,
                    properties={
                        "code": boundary.code,
                        "name": boundary.name,
                        "level": boundary.level,
                        "boundary_version": boundary.boundary_version,
                    },
                )
            )
        return features, False

    # ------------------------------------------------------------- internals

    def _require_scope(self, query: MapQuery) -> None:
        if not query.crop or not query.target:
            raise MapUnavailable("scope_required")

    def _require_boundary_version(self, version: str) -> None:
        if version != self._policy.boundary_version:
            raise MapUnavailable("boundary_version_mismatch")

    def _matches(
        self, item: ReportAggregate | ForecastArea | CoverageArea, query: MapQuery
    ) -> bool:
        if item.crop_code != query.crop or item.target_code != query.target:
            return False
        if query.bbox is not None and not _intersects(item.geometry, query.bbox):
            return False
        if query.on_date is not None:
            at = datetime.combine(query.on_date, time.min, tzinfo=UTC)
            if isinstance(item, ReportAggregate):
                if not (item.window_from <= at < item.window_to):
                    return False
            elif not (item.valid_from <= at < item.valid_to):
                return False
        return True

    def _suppress_count(self, count: int) -> tuple[int | None, bool]:
        if count < self._policy.small_count_threshold:
            return None, True
        return count, False

    def _suppress_detail(self, detail: dict[str, int]) -> tuple[dict[str, int | None], bool]:
        suppressed = False
        exposed: dict[str, int | None] = {}
        for key, value in detail.items():
            if value < self._policy.small_count_threshold:
                exposed[key] = None
                suppressed = True
            else:
                exposed[key] = value
        return exposed, suppressed

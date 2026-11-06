"""Synthetic map fixtures.

Every coordinate, count, threshold and boundary version here is a labelled test
fixture. None is a production geography, suppression value or approved policy.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.modules.mapping.models import (
    BBox,
    BoundaryFeature,
    CoverageArea,
    ForecastArea,
    LineStringGeometry,
    MapPolicy,
    MapQuery,
    PointGeometry,
    PolygonGeometry,
    ReportAggregate,
)
from app.modules.mapping.service import MapService
from app.modules.mapping.store import MapDataStore

NOW = datetime(2026, 11, 6, 8, 0, 0, tzinfo=UTC)
BOUNDARY_VERSION = "bv-test-1"


class FixedClock:
    def __init__(self, now: datetime = NOW) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def make_policy(
    *,
    small_count_threshold: int = 5,
    boundary_version: str = BOUNDARY_VERSION,
    probability_approved: bool = False,
    verified_statuses: frozenset[str] = frozenset({"confirmed", "probable"}),
    unverified_statuses: frozenset[str] = frozenset({"unverified", "needs_visit"}),
) -> MapPolicy:
    return MapPolicy(
        boundary_version=boundary_version,
        aggregation_level="block",
        small_count_threshold=small_count_threshold,
        verified_statuses=verified_statuses,
        unverified_statuses=unverified_statuses,
        probability_approved=probability_approved,
        approved_by="synthetic-reviewer",
        approved_at=NOW - timedelta(days=1),
    )


def point() -> PointGeometry:
    return PointGeometry(coordinates=(10.0, 20.0))


def polygon(x: float = 10.0, y: float = 20.0) -> PolygonGeometry:
    return PolygonGeometry(
        coordinates=[
            [
                (x - 1.0, y - 1.0),
                (x + 1.0, y - 1.0),
                (x + 1.0, y + 1.0),
                (x - 1.0, y + 1.0),
                (x - 1.0, y - 1.0),
            ]
        ]
    )


def make_report(
    *,
    aggregate_id: str = "agg-1",
    status: str = "confirmed",
    count: int = 8,
    x: float = 10.0,
    y: float = 20.0,
    crop: str = "crop-1",
    target: str = "target-1",
) -> ReportAggregate:
    return ReportAggregate(
        aggregate_id=aggregate_id,
        geo_code=f"area-{aggregate_id}",
        geometry=PointGeometry(coordinates=(x, y)),
        verification_status=status,
        count=count,
        crop_code=crop,
        target_code=target,
        window_from=NOW - timedelta(days=1),
        window_to=NOW + timedelta(days=1),
        observed_at=NOW,
        is_demo=True,
    )


def make_forecast(
    *,
    forecast_id: str = "fcst-1",
    band: str = "high",
    probability: float | None = 0.7,
    coverage: float = 0.8,
    coverage_detail: dict[str, int] | None = None,
    x: float = 10.0,
    y: float = 20.0,
    boundary_version: str = BOUNDARY_VERSION,
    crop: str = "crop-1",
    target: str = "target-1",
) -> ForecastArea:
    return ForecastArea(
        forecast_id=forecast_id,
        geo_code=f"area-{forecast_id}",
        geometry=polygon(x, y),
        crop_code=crop,
        target_code=target,
        band=band,
        probability=probability,
        coverage=coverage,
        coverage_detail=coverage_detail or {"verified_reports_14d": 4, "active_reporters": 7},
        drivers=("rainfall", "humidity"),
        model_version="synthetic-rules-0.1",
        issue_time=NOW,
        valid_from=NOW - timedelta(days=1),
        valid_to=NOW + timedelta(days=7),
        is_stale=False,
        is_demo=True,
        boundary_version=boundary_version,
    )


def make_coverage(
    *,
    coverage: float = 0.8,
    boundary_version: str = BOUNDARY_VERSION,
) -> CoverageArea:
    return CoverageArea(
        geo_code="area-1",
        geometry=polygon(),
        crop_code="crop-1",
        target_code="target-1",
        coverage=coverage,
        coverage_detail={"active_reporters": 7, "verified_reports_14d": 4},
        valid_from=NOW - timedelta(days=1),
        valid_to=NOW + timedelta(days=7),
        computed_at=NOW,
        boundary_version=boundary_version,
    )


def make_boundary(boundary_version: str = BOUNDARY_VERSION) -> BoundaryFeature:
    return BoundaryFeature(
        code="area-1",
        name="Synthetic Block",
        level="block",
        geometry=LineStringGeometry(coordinates=[(9.0, 19.0), (11.0, 21.0)]),
        boundary_version=boundary_version,
    )


def make_query(
    *,
    crop: str | None = "crop-1",
    target: str | None = "target-1",
    on_date=None,
    bbox: BBox | None = None,
) -> MapQuery:
    return MapQuery(crop=crop, target=target, on_date=on_date, bbox=bbox)


def make_store(boundary_version: str = BOUNDARY_VERSION) -> MapDataStore:
    store = MapDataStore()
    store.add_report(make_report(aggregate_id="confirmed-1", status="confirmed", count=8))
    store.add_report(make_report(aggregate_id="probable-1", status="probable", count=3, x=10.1))
    store.add_report(make_report(aggregate_id="rejected-1", status="rejected", count=9, x=10.2))
    store.add_report(make_report(aggregate_id="duplicate-1", status="duplicate", count=9, x=10.3))
    store.add_report(make_report(aggregate_id="unverified-1", status="unverified", count=2, x=10.4))
    store.add_report(
        make_report(aggregate_id="needs-visit-1", status="needs_visit", count=6, x=10.5)
    )
    store.add_forecast(make_forecast(forecast_id="scored-1"))
    store.add_forecast(
        make_forecast(
            forecast_id="insufficient-1",
            band="insufficient_data",
            probability=None,
            coverage=0.2,
            coverage_detail={"active_reporters": 2},
            x=12.0,
        )
    )
    store.add_forecast(make_forecast(forecast_id="far-low", band="low", x=50.0, y=50.0))
    store.add_coverage(make_coverage())
    store.add_boundary(make_boundary(boundary_version))
    return store


def make_service(
    *,
    store: MapDataStore | None = None,
    policy: MapPolicy | None = None,
    clock=None,
) -> MapService:
    return MapService(
        store=store or make_store(),
        policy=policy or make_policy(),
        clock=clock or FixedClock(),
    )

"""Map layer contract (spec 06 §7–§8).

Each layer is a separate GeoJSON FeatureCollection. No model here can represent
a merged "risk" layer: the layer name is a closed set and every layer carries
its own property model.

Geometry is always supplied by a repository. Nothing in this module invents a
coordinate, boundary, centroid or aggregate.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

LayerName = Literal[
    "verified_reports",
    "unverified_reports",
    "modelled_risk",
    "coverage",
    "boundaries",
]
LAYERS: frozenset[str] = frozenset(
    {"verified_reports", "unverified_reports", "modelled_risk", "coverage", "boundaries"}
)

VerificationStatus = Literal[
    "confirmed",
    "probable",
    "rejected",
    "duplicate",
    "needs_visit",
    "unresolved",
    "unverified",
]

RiskBand = Literal["low", "moderate", "high", "urgent", "insufficient_data"]


class PointGeometry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]


class LineStringGeometry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["LineString"] = "LineString"
    coordinates: list[tuple[float, float]] = Field(min_length=2)


class PolygonGeometry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[tuple[float, float]]] = Field(min_length=1)


class MultiPolygonGeometry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["MultiPolygon"] = "MultiPolygon"
    coordinates: list[list[list[tuple[float, float]]]] = Field(min_length=1)


AreaGeometry = Annotated[
    PolygonGeometry | MultiPolygonGeometry,
    Field(discriminator="type"),
]
LineGeometry = Annotated[
    LineStringGeometry | PolygonGeometry | MultiPolygonGeometry,
    Field(discriminator="type"),
]
Geometry = Annotated[
    PointGeometry | PolygonGeometry | MultiPolygonGeometry | LineStringGeometry,
    Field(discriminator="type"),
]


class BBox(BaseModel):
    """Inclusive map viewport. Longitudes and latitudes are validated."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    min_lon: float = Field(ge=-180, le=180)
    min_lat: float = Field(ge=-90, le=90)
    max_lon: float = Field(ge=-180, le=180)
    max_lat: float = Field(ge=-90, le=90)

    @model_validator(mode="after")
    def _ordered(self) -> BBox:
        if self.min_lon >= self.max_lon:
            raise ValueError("min_lon must be less than max_lon")
        if self.min_lat >= self.max_lat:
            raise ValueError("min_lat must be less than max_lat")
        return self

    @classmethod
    def parse(cls, value: str) -> BBox:
        parts = value.split(",")
        if len(parts) != 4:
            raise ValueError("bbox must be min_lon,min_lat,max_lon,max_lat")
        try:
            numbers = [float(part) for part in parts]
        except ValueError as error:
            raise ValueError("bbox values must be numbers") from error
        return cls(
            min_lon=numbers[0],
            min_lat=numbers[1],
            max_lon=numbers[2],
            max_lat=numbers[3],
        )


class MapQuery(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    crop: str | None = Field(default=None, max_length=80)
    target: str | None = Field(default=None, max_length=80)
    on_date: date | None = None
    bbox: BBox | None = None


class MapPolicy(BaseModel):
    """Approved map configuration.

    Every field is supplied by a deployment. There is no default suppression
    threshold, aggregation level or verified-state set, because D9 is unresolved
    and a code default would become policy.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    boundary_version: str = Field(min_length=1, max_length=120)
    aggregation_level: str = Field(min_length=1, max_length=80)
    small_count_threshold: int = Field(ge=1)
    verified_statuses: frozenset[VerificationStatus] = Field(min_length=1)
    unverified_statuses: frozenset[VerificationStatus] = Field(min_length=1)
    probability_approved: bool
    approved_by: str = Field(min_length=1, max_length=120)
    approved_at: AwareDatetime

    @model_validator(mode="after")
    def _consistent(self) -> MapPolicy:
        if self.verified_statuses & self.unverified_statuses:
            raise ValueError("verified and unverified statuses must be disjoint")
        forbidden = {"rejected", "duplicate"}
        if self.verified_statuses & forbidden:
            raise ValueError("rejected and duplicate reports cannot be verified")
        if self.unverified_statuses & forbidden:
            raise ValueError("rejected and duplicate reports cannot be unverified")
        return self


class ReportAggregate(BaseModel):
    """One aggregated report symbol at the supported aggregation level."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    aggregate_id: str = Field(min_length=1, max_length=120)
    geo_code: str = Field(min_length=1, max_length=80)
    geometry: PointGeometry
    verification_status: VerificationStatus
    count: int = Field(ge=1)
    crop_code: str = Field(min_length=1, max_length=80)
    target_code: str = Field(min_length=1, max_length=80)
    window_from: AwareDatetime
    window_to: AwareDatetime
    observed_at: AwareDatetime
    is_demo: bool = False

    @model_validator(mode="after")
    def _window(self) -> ReportAggregate:
        if self.window_to <= self.window_from:
            raise ValueError("window_to must be after window_from")
        return self


class ForecastArea(BaseModel):
    """Persisted forecast polygon. The map never computes a band."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    forecast_id: str = Field(min_length=1, max_length=120)
    geo_code: str = Field(min_length=1, max_length=80)
    geometry: AreaGeometry
    crop_code: str = Field(min_length=1, max_length=80)
    target_code: str = Field(min_length=1, max_length=80)
    band: RiskBand
    probability: float | None = Field(default=None, ge=0, le=1)
    coverage: float = Field(ge=0, le=1)
    coverage_detail: dict[str, int] = Field(default_factory=dict)
    drivers: tuple[str, ...] = ()
    model_version: str = Field(min_length=1, max_length=120)
    issue_time: AwareDatetime
    valid_from: AwareDatetime
    valid_to: AwareDatetime
    is_stale: bool
    is_demo: bool = False
    boundary_version: str = Field(min_length=1, max_length=120)

    @model_validator(mode="after")
    def _window(self) -> ForecastArea:
        if self.valid_to <= self.valid_from:
            raise ValueError("valid_to must be after valid_from")
        return self


class CoverageArea(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    geo_code: str = Field(min_length=1, max_length=80)
    geometry: AreaGeometry
    crop_code: str = Field(min_length=1, max_length=80)
    target_code: str = Field(min_length=1, max_length=80)
    coverage: float = Field(ge=0, le=1)
    coverage_detail: dict[str, int] = Field(default_factory=dict)
    valid_from: AwareDatetime
    valid_to: AwareDatetime
    computed_at: AwareDatetime
    boundary_version: str = Field(min_length=1, max_length=120)

    @model_validator(mode="after")
    def _window(self) -> CoverageArea:
        if self.valid_to <= self.valid_from:
            raise ValueError("valid_to must be after valid_from")
        return self


class BoundaryFeature(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    level: str = Field(min_length=1, max_length=80)
    geometry: LineGeometry
    boundary_version: str = Field(min_length=1, max_length=120)


class MapFeature(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["Feature"] = "Feature"
    geometry: Geometry
    properties: dict[str, Any]


class MapLayerResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["FeatureCollection"] = "FeatureCollection"
    layer: LayerName
    boundary_version: str
    generated_at: AwareDatetime
    aggregation_level: str
    features: list[MapFeature]
    empty: bool
    empty_message: str | None
    small_count_suppression_applied: bool


class MapUnavailable(ValueError):
    """A typed refusal to serve a layer. Carries a machine-readable code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code

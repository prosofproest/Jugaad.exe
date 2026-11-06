"""
CropSentinel AI — Domain 8: Hotspot and Outbreak Database
Tables:
- pest_reports
- verified_cases
- hotspot_regions
- regional_pest_statistics
- outbreak_predictions
- spread_observations
- risk_history
- monitoring_coverage
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import (
    Base,
    PortableUUID,
    PostGISGeometry,
    TimestampMixin,
)


class PestReport(Base, TimestampMixin):
    """Field reports submitted by farmers or extension scouts."""
    __tablename__ = "pest_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    farm_plot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("farm_plots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reported_pest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reported_disease_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("diseases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    report_location: Mapped[str] = mapped_column(
        PostGISGeometry("POINT", 4326),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(String(20), default="moderate", nullable=False)
    observation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="unverified", nullable=False)

    __table_args__ = (
        CheckConstraint(
            "severity IN ('low', 'moderate', 'high', 'severe')",
            name="chk_pest_reports_severity",
        ),
        CheckConstraint(
            "status IN ('unverified', 'under_investigation', 'verified', 'rejected')",
            name="chk_pest_reports_status",
        ),
        CheckConstraint(
            "reported_pest_id IS NOT NULL OR reported_disease_id IS NOT NULL",
            name="chk_pest_report_target_present",
        ),
        Index("idx_pest_reports_geom", "report_location", postgresql_using="gist"),
    )

    reporter: Mapped["User"] = relationship("User")
    plot: Mapped[Optional["FarmPlot"]] = relationship("FarmPlot")
    reported_pest: Mapped[Optional["Pest"]] = relationship("Pest")
    reported_disease: Mapped[Optional["Disease"]] = relationship("Disease")
    verified_case: Mapped[Optional["VerifiedCase"]] = relationship(
        "VerifiedCase", back_populates="report", uselist=False
    )


class VerifiedCase(Base, TimestampMixin):
    """Ground-truth verified infestation case confirmed by an agronomist or pathologist."""
    __tablename__ = "verified_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    pest_report_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("pest_reports.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    verifier_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    confirmed_location: Mapped[str] = mapped_column(
        PostGISGeometry("POINT", 4326),
        nullable=False,
    )
    confirmed_pest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    confirmed_disease_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("diseases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    confidence_level: Mapped[str] = mapped_column(String(20), default="high", nullable=False)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "confidence_level IN ('tentative', 'moderate', 'high', 'laboratory_confirmed')",
            name="chk_verified_cases_conf",
        ),
        Index("idx_verified_cases_geom", "confirmed_location", postgresql_using="gist"),
    )

    report: Mapped["PestReport"] = relationship("PestReport", back_populates="verified_case")
    verifier: Mapped["User"] = relationship("User")
    confirmed_pest: Mapped[Optional["Pest"]] = relationship("Pest")
    confirmed_disease: Mapped[Optional["Disease"]] = relationship("Disease")


class HotspotRegion(Base, TimestampMixin):
    """Spatially identified pest/disease outbreak hotspot zone."""
    __tablename__ = "hotspot_regions"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    region_name: Mapped[str] = mapped_column(String(150), nullable=False)
    boundary_geom: Mapped[str] = mapped_column(
        PostGISGeometry("MULTIPOLYGON", 4326),
        nullable=False,
    )
    pest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    disease_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("diseases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    risk_level: Mapped[str] = mapped_column(String(20), default="moderate", nullable=False)
    active_case_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "risk_level IN ('low', 'moderate', 'high', 'extreme')",
            name="chk_hotspot_risk_level",
        ),
        CheckConstraint("active_case_count >= 0", name="chk_hotspot_cases_nonneg"),
        Index("idx_hotspot_regions_geom", "boundary_geom", postgresql_using="gist"),
    )

    pest: Mapped[Optional["Pest"]] = relationship("Pest")
    disease: Mapped[Optional["Disease"]] = relationship("Disease")
    spread_observations: Mapped[List["SpreadObservation"]] = relationship(
        "SpreadObservation", back_populates="hotspot", cascade="all, delete-orphan"
    )


class RegionalPestStatistic(Base):
    """Periodic statistical rollup for a region or administrative block."""
    __tablename__ = "regional_pest_statistics"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    region_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    date_bucket: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    pest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="SET NULL"),
        nullable=True,
    )
    disease_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("diseases.id", ondelete="SET NULL"),
        nullable=True,
    )
    total_reports: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incidence_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_severity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("region_code", "date_bucket", "pest_id", "disease_id", name="uq_reg_pest_stat_bucket"),
    )


class OutbreakPrediction(Base):
    """
    Predictive outbreak risk polygons generated by epidemiological models.
    Append-only: records historical forecast runs with exact model lineage.
    """
    __tablename__ = "outbreak_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    region_geom: Mapped[str] = mapped_column(
        PostGISGeometry("POLYGON", 4326),
        nullable=False,
    )
    pest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    disease_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("diseases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    predicted_risk_score: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=False,
    )
    forecast_horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    prediction_model_version: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("ai_model_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    prediction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "predicted_risk_score >= 0.0000 AND predicted_risk_score <= 1.0000",
            name="chk_outbreak_risk_range",
        ),
        CheckConstraint("forecast_horizon_days > 0", name="chk_outbreak_horizon_pos"),
        Index("idx_outbreak_predictions_geom", "region_geom", postgresql_using="gist"),
    )

    pest: Mapped[Optional["Pest"]] = relationship("Pest")
    disease: Mapped[Optional["Disease"]] = relationship("Disease")
    model_version: Mapped[Optional["AIModelVersion"]] = relationship("AIModelVersion")


class SpreadObservation(Base):
    """Vector and rate of geographical spread observed between intervals."""
    __tablename__ = "spread_observations"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    hotspot_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("hotspot_regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observation_location: Mapped[str] = mapped_column(
        PostGISGeometry("POINT", 4326),
        nullable=False,
    )
    spread_direction_degrees: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spread_rate_km_per_day: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorder_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "spread_direction_degrees IS NULL OR (spread_direction_degrees >= 0 AND spread_direction_degrees <= 360)",
            name="chk_spread_direction_degrees",
        ),
        Index("idx_spread_obs_geom", "observation_location", postgresql_using="gist"),
    )

    hotspot: Mapped["HotspotRegion"] = relationship("HotspotRegion", back_populates="spread_observations")
    recorder: Mapped["User"] = relationship("User")


class RiskHistory(Base):
    """Audit log of calculated regional risk scores over time."""
    __tablename__ = "risk_history"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    region_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    pest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="SET NULL"),
        nullable=True,
    )
    historical_risk_score: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=False,
    )
    weather_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_run_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "historical_risk_score >= 0.0000 AND historical_risk_score <= 1.0000",
            name="chk_risk_hist_score_range",
        ),
    )


class MonitoringCoverage(Base, TimestampMixin):
    """Field scouting coverage and surveillance footprint for a sector."""
    __tablename__ = "monitoring_coverage"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    area_name: Mapped[str] = mapped_column(String(150), nullable=False)
    boundary: Mapped[str] = mapped_column(
        PostGISGeometry("POLYGON", 4326),
        nullable=False,
    )
    assigned_scouts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scouting_frequency_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    last_monitored_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    coverage_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "coverage_percentage >= 0.0 AND coverage_percentage <= 100.0",
            name="chk_monitoring_coverage_pct",
        ),
        Index("idx_monitoring_coverage_geom", "boundary", postgresql_using="gist"),
    )


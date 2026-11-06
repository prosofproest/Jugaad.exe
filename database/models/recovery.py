"""
CropSentinel AI — Domain 9: Recovery and Inspection Database
Tables:
- inspections
- inspection_assignments
- scouting_records
- recovery_records
- recovery_comparisons
- seasonal_history
- infestation_history
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


class Inspection(Base, TimestampMixin):
    """Farm inspection and scouting events."""
    __tablename__ = "inspections"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("farm_plots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    inspector_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    conducted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="scheduled", nullable=False)
    overall_health_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    findings_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled', 'rescheduled')",
            name="chk_inspections_status",
        ),
        CheckConstraint(
            "overall_health_rating IS NULL OR (overall_health_rating >= 1 AND overall_health_rating <= 5)",
            name="chk_inspections_health_rating",
        ),
    )

    farm: Mapped["Farm"] = relationship("Farm")
    plot: Mapped[Optional["FarmPlot"]] = relationship("FarmPlot")
    inspector: Mapped["User"] = relationship("User")
    assignments: Mapped[List["InspectionAssignment"]] = relationship(
        "InspectionAssignment", back_populates="inspection", cascade="all, delete-orphan"
    )
    scouting_records: Mapped[List["ScoutingRecord"]] = relationship(
        "ScoutingRecord", back_populates="inspection", cascade="all, delete-orphan"
    )


class InspectionAssignment(Base):
    """Field agents assigned to execute an inspection."""
    __tablename__ = "inspection_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_by: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    role_in_inspection: Mapped[str] = mapped_column(String(50), default="lead_scout", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="assigned", nullable=False)

    __table_args__ = (
        UniqueConstraint("inspection_id", "agent_id", name="uq_inspection_agent"),
        CheckConstraint(
            "status IN ('assigned', 'accepted', 'declined', 'completed')",
            name="chk_insp_assign_status",
        ),
    )

    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="assignments")
    agent: Mapped["User"] = relationship("User", foreign_keys=[agent_id])
    assigner: Mapped["User"] = relationship("User", foreign_keys=[assigned_by])


class ScoutingRecord(Base):
    """Waypoints, plant counts, and scouting observations along transect lines."""
    __tablename__ = "scouting_records"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    waypoint_location: Mapped[str] = mapped_column(
        PostGISGeometry("POINT", 4326),
        nullable=False,
    )
    plant_count_inspected: Mapped[int] = mapped_column(Integer, nullable=False)
    infested_plant_count: Mapped[int] = mapped_column(Integer, nullable=False)
    pest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("plant_count_inspected >= 0", name="chk_scouting_inspected_nonneg"),
        CheckConstraint("infested_plant_count >= 0 AND infested_plant_count <= plant_count_inspected", name="chk_scouting_infested_bounds"),
        Index("idx_scouting_records_geom", "waypoint_location", postgresql_using="gist"),
    )

    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="scouting_records")
    pest: Mapped[Optional["Pest"]] = relationship("Pest")


class RecoveryRecord(Base, TimestampMixin):
    """Tracking plant recovery trajectory following remediation/treatment."""
    __tablename__ = "recovery_records"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    farm_plot_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("farm_plots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    crop_instance_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("crop_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    treatment_record_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("treatment_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    inspection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("inspections.id", ondelete="SET NULL"),
        nullable=True,
    )
    recovery_status: Mapped[str] = mapped_column(String(30), nullable=False)
    recovery_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    assessor_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "recovery_status IN ('worsening', 'stable', 'partial_recovery', 'full_recovery')",
            name="chk_recovery_status_valid",
        ),
        CheckConstraint(
            "recovery_percentage >= 0.0 AND recovery_percentage <= 100.0",
            name="chk_recovery_pct_range",
        ),
    )

    plot: Mapped["FarmPlot"] = relationship("FarmPlot")
    crop_instance: Mapped["CropInstance"] = relationship("CropInstance")
    treatment_record: Mapped[Optional["TreatmentRecord"]] = relationship("TreatmentRecord")
    inspection: Mapped[Optional["Inspection"]] = relationship("Inspection")
    assessor: Mapped["User"] = relationship("User")
    comparisons: Mapped[List["RecoveryComparison"]] = relationship(
        "RecoveryComparison", back_populates="recovery_record", cascade="all, delete-orphan"
    )


class RecoveryComparison(Base, TimestampMixin):
    """Before/after visual and physiological comparison."""
    __tablename__ = "recovery_comparisons"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    recovery_record_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("recovery_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    baseline_media_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("media_files.id", ondelete="RESTRICT"),
        nullable=False,
    )
    current_media_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("media_files.id", ondelete="RESTRICT"),
        nullable=False,
    )
    symptom_reduction_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    foliage_regrowth_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comparison_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "symptom_reduction_percentage IS NULL OR (symptom_reduction_percentage >= 0.0 AND symptom_reduction_percentage <= 100.0)",
            name="chk_rec_comp_reduction_pct",
        ),
        CheckConstraint(
            "foliage_regrowth_score IS NULL OR (foliage_regrowth_score >= 1 AND foliage_regrowth_score <= 5)",
            name="chk_rec_comp_regrowth_score",
        ),
    )

    recovery_record: Mapped["RecoveryRecord"] = relationship("RecoveryRecord", back_populates="comparisons")
    baseline_media: Mapped["MediaFile"] = relationship("MediaFile", foreign_keys=[baseline_media_id])
    current_media: Mapped["MediaFile"] = relationship("MediaFile", foreign_keys=[current_media_id])


class SeasonalHistory(Base):
    """Historical seasonal performance and pest pressure records."""
    __tablename__ = "seasonal_history"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    farm_plot_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("farm_plots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    season_year: Mapped[int] = mapped_column(Integer, nullable=False)
    season_name: Mapped[str] = mapped_column(String(30), nullable=False)
    crop_type_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("crop_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    total_yield_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pest_pressure_rating: Mapped[str] = mapped_column(String(20), default="low", nullable=False)
    weather_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("farm_plot_id", "season_year", "season_name", name="uq_seasonal_hist_plot_season"),
        CheckConstraint(
            "season_name IN ('kharif', 'rabi', 'zaid', 'annual')",
            name="chk_seasonal_hist_season",
        ),
        CheckConstraint(
            "pest_pressure_rating IN ('none', 'low', 'moderate', 'high', 'severe')",
            name="chk_seasonal_hist_pest_pressure",
        ),
    )

    plot: Mapped["FarmPlot"] = relationship("FarmPlot")
    crop_type: Mapped["CropType"] = relationship("CropType")


class InfestationHistory(Base):
    """Retrospective timeline of outbreaks on a farm plot."""
    __tablename__ = "infestation_history"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    farm_plot_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("farm_plots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    crop_instance_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("crop_instances.id", ondelete="SET NULL"),
        nullable=True,
    )
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
    outbreak_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    peak_severity: Mapped[str] = mapped_column(String(20), nullable=False)
    containment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    crop_loss_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "crop_loss_percentage IS NULL OR (crop_loss_percentage >= 0.0 AND crop_loss_percentage <= 100.0)",
            name="chk_infest_hist_loss_range",
        ),
    )

    plot: Mapped["FarmPlot"] = relationship("FarmPlot")
    crop_instance: Mapped[Optional["CropInstance"]] = relationship("CropInstance")
    pest: Mapped[Optional["Pest"]] = relationship("Pest")
    disease: Mapped[Optional["Disease"]] = relationship("Disease")


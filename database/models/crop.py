"""
CropSentinel AI — Domain 3: Crop and Plant Database
Tables:
- crop_types
- crop_groups
- crop_instances
- plants
- plant_observations
- crop_growth_stages
- planting_records
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


class CropGroup(Base, TimestampMixin):
    """Broad agricultural classification (cereals, pulses, vegetables, oilseeds, fruits)."""
    __tablename__ = "crop_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    crop_types: Mapped[List["CropType"]] = relationship("CropType", back_populates="group")


class CropType(Base, TimestampMixin):
    """Crop master definition."""
    __tablename__ = "crop_types"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("crop_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    common_name: Mapped[str] = mapped_column(String(100), nullable=False)
    botanical_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    optimal_temp_min_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    optimal_temp_max_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    optimal_rainfall_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    group: Mapped[Optional["CropGroup"]] = relationship("CropGroup", back_populates="crop_types")
    growth_stages: Mapped[List["CropGrowthStage"]] = relationship(
        "CropGrowthStage", back_populates="crop_type", cascade="all, delete-orphan"
    )
    crop_instances: Mapped[List["CropInstance"]] = relationship("CropInstance", back_populates="crop_type")


class CropGrowthStage(Base):
    """Growth and phenological stages for a crop type."""
    __tablename__ = "crop_growth_stages"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    crop_type_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("crop_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage_name: Mapped[str] = mapped_column(String(50), nullable=False)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False)
    typical_duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    water_requirement_level: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("crop_type_id", "stage_order", name="uq_crop_stage_order"),
        UniqueConstraint("crop_type_id", "stage_name", name="uq_crop_stage_name"),
        CheckConstraint("typical_duration_days > 0", name="chk_crop_stage_duration"),
        CheckConstraint(
            "water_requirement_level IN ('low', 'medium', 'high', 'critical')",
            name="chk_crop_stage_water_req",
        ),
    )

    crop_type: Mapped["CropType"] = relationship("CropType", back_populates="growth_stages")


class CropInstance(Base, TimestampMixin):
    """Crops planted in a specific farm plot."""
    __tablename__ = "crop_instances"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    plot_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("farm_plots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    crop_type_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("crop_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    variety: Mapped[str] = mapped_column(String(100), nullable=False)
    season: Mapped[str] = mapped_column(String(30), nullable=False)
    planting_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_harvest_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_harvest_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('planned', 'active', 'harvested', 'failed', 'rotated')",
            name="chk_crop_instance_status",
        ),
        CheckConstraint(
            "season IN ('kharif', 'rabi', 'zaid', 'summer', 'perennial')",
            name="chk_crop_instance_season",
        ),
    )

    crop_type: Mapped["CropType"] = relationship("CropType", back_populates="crop_instances")
    plants: Mapped[List["Plant"]] = relationship(
        "Plant", back_populates="crop_instance", cascade="all, delete-orphan"
    )
    planting_records: Mapped[List["PlantingRecord"]] = relationship(
        "PlantingRecord", back_populates="crop_instance", cascade="all, delete-orphan"
    )


class Plant(Base, TimestampMixin):
    """Individual plant record tracked within a crop instance."""
    __tablename__ = "plants"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    crop_instance_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("crop_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag_or_id: Mapped[str] = mapped_column(String(50), nullable=False)
    row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    column_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    plant_location: Mapped[Optional[str]] = mapped_column(
        PostGISGeometry("POINT", 4326),
        nullable=True,
    )
    health_status: Mapped[str] = mapped_column(String(30), default="healthy", nullable=False)
    planted_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    __table_args__ = (
        UniqueConstraint("crop_instance_id", "tag_or_id", name="uq_plant_crop_instance_tag"),
        CheckConstraint(
            "health_status IN ('healthy', 'stressed', 'infested', 'diseased', 'deceased', 'recovered')",
            name="chk_plants_health_status",
        ),
        Index("idx_plants_geom", "plant_location", postgresql_using="gist"),
    )

    crop_instance: Mapped["CropInstance"] = relationship("CropInstance", back_populates="plants")
    observations: Mapped[List["PlantObservation"]] = relationship(
        "PlantObservation", back_populates="plant", cascade="all, delete-orphan"
    )


class PlantObservation(Base):
    """Individual plant health and visual observation."""
    __tablename__ = "plant_observations"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    plant_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observer_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    observation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    visual_symptoms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vigor_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    foliage_damage_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    observation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("vigor_score IS NULL OR (vigor_score >= 1 AND vigor_score <= 10)", name="chk_plant_obs_vigor"),
        CheckConstraint("foliage_damage_pct IS NULL OR (foliage_damage_pct >= 0 AND foliage_damage_pct <= 100)", name="chk_plant_obs_damage_pct"),
    )

    plant: Mapped["Plant"] = relationship("Plant", back_populates="observations")
    observer: Mapped["User"] = relationship("User")


class PlantingRecord(Base):
    """Detailed planting operation details for a crop instance."""
    __tablename__ = "planting_records"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    crop_instance_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("crop_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seed_lot_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    seed_source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    sowing_method: Mapped[str] = mapped_column(String(50), default="direct_seeding", nullable=False)
    planting_density_per_sqm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fertilization_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "sowing_method IN ('direct_seeding', 'transplanting', 'broadcasting', 'dibbling', 'drilling')",
            name="chk_planting_record_sowing_method",
        ),
    )

    crop_instance: Mapped["CropInstance"] = relationship("CropInstance", back_populates="planting_records")
    recorder: Mapped["User"] = relationship("User")


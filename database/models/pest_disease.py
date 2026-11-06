"""
CropSentinel AI — Domain 5: Pest and Disease Database
Tables:
- pests
- pest_categories
- pest_life_cycles
- pest_host_crops
- diseases
- disease_symptoms
- crop_symptoms
- pest_damage_records
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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
    TimestampMixin,
)


class PestCategory(Base, TimestampMixin):
    """Broad biological classification (insects, mites, nematodes, rodents, molluscs)."""
    __tablename__ = "pest_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    pests: Mapped[List["Pest"]] = relationship("Pest", back_populates="category")


class Pest(Base, TimestampMixin):
    """Pest master record."""
    __tablename__ = "pests"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    pest_category_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("pest_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    common_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    scientific_name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    identification_guide: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    economic_threshold: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quarantine_status: Mapped[str] = mapped_column(String(30), default="non_quarantine", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "quarantine_status IN ('non_quarantine', 'regulated_non_quarantine', 'quarantine_pest', 'priority_pest')",
            name="chk_pests_quarantine_status",
        ),
    )

    category: Mapped["PestCategory"] = relationship("PestCategory", back_populates="pests")
    life_cycles: Mapped[List["PestLifeCycle"]] = relationship(
        "PestLifeCycle", back_populates="pest", cascade="all, delete-orphan"
    )
    host_crops: Mapped[List["PestHostCrop"]] = relationship(
        "PestHostCrop", back_populates="pest", cascade="all, delete-orphan"
    )
    damage_records: Mapped[List["PestDamageRecord"]] = relationship(
        "PestDamageRecord", back_populates="pest", cascade="all, delete-orphan"
    )


class PestLifeCycle(Base):
    """Biological developmental stages for a pest."""
    __tablename__ = "pest_life_cycles"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    pest_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage_name: Mapped[str] = mapped_column(String(50), nullable=False)
    stage_duration_days_min: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_duration_days_max: Mapped[int] = mapped_column(Integer, nullable=False)
    damaging_stage: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    favorable_temperature_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    favorable_temperature_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    favorable_humidity_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("pest_id", "stage_name", name="uq_pest_lifecycle_stage"),
        CheckConstraint("stage_duration_days_min >= 0", name="chk_pest_stage_dur_min"),
        CheckConstraint("stage_duration_days_max >= stage_duration_days_min", name="chk_pest_stage_dur_max"),
    )

    pest: Mapped["Pest"] = relationship("Pest", back_populates="life_cycles")


class PestHostCrop(Base):
    """Many-to-many relationship linking pests to host crops."""
    __tablename__ = "pest_host_crops"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    pest_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    crop_type_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("crop_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    susceptibility_level: Mapped[str] = mapped_column(String(30), default="primary", nullable=False)
    damage_severity_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("pest_id", "crop_type_id", name="uq_pest_host_crops_pair"),
        CheckConstraint(
            "susceptibility_level IN ('primary', 'secondary', 'accidental', 'resistant')",
            name="chk_pest_host_susceptibility",
        ),
        CheckConstraint(
            "damage_severity_rating IS NULL OR (damage_severity_rating >= 1 AND damage_severity_rating <= 5)",
            name="chk_pest_host_severity_rating",
        ),
    )

    pest: Mapped["Pest"] = relationship("Pest", back_populates="host_crops")
    crop_type: Mapped["CropType"] = relationship("CropType")


class Disease(Base, TimestampMixin):
    """Plant pathogen and disease master record."""
    __tablename__ = "diseases"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    common_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    scientific_name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    pathogen_type: Mapped[str] = mapped_column(String(50), nullable=False)
    vector_pest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    favorable_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    economic_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "pathogen_type IN ('fungal', 'bacterial', 'viral', 'viroid', 'phytoplasma', 'oomycete', 'nematode', 'abiotic')",
            name="chk_diseases_pathogen_type",
        ),
    )

    vector_pest: Mapped[Optional["Pest"]] = relationship("Pest")
    symptoms: Mapped[List["DiseaseSymptom"]] = relationship(
        "DiseaseSymptom", back_populates="disease", cascade="all, delete-orphan"
    )


class DiseaseSymptom(Base):
    """Specific symptoms manifested by a disease."""
    __tablename__ = "disease_symptoms"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    disease_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("diseases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    affected_plant_part: Mapped[str] = mapped_column(String(50), nullable=False)
    symptom_description: Mapped[str] = mapped_column(Text, nullable=False)
    severity_scale: Mapped[str] = mapped_column(String(20), default="moderate", nullable=False)
    is_primary_symptom: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "affected_plant_part IN ('leaf', 'stem', 'root', 'fruit', 'flower', 'crown', 'whole_plant', 'vascular_system')",
            name="chk_disease_symptoms_plant_part",
        ),
    )

    disease: Mapped["Disease"] = relationship("Disease", back_populates="symptoms")


class CropSymptom(Base):
    """Crop-specific manifestation of pests and diseases."""
    __tablename__ = "crop_symptoms"

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
    disease_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("diseases.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    pest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    symptom_name: Mapped[str] = mapped_column(String(150), nullable=False)
    characteristic_appearance: Mapped[Text] = mapped_column(Text, nullable=False)
    typical_growth_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    visual_diagnostic_rules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "disease_id IS NOT NULL OR pest_id IS NOT NULL",
            name="chk_crop_symptoms_agent_present",
        ),
    )

    crop_type: Mapped["CropType"] = relationship("CropType")
    disease: Mapped[Optional["Disease"]] = relationship("Disease")
    pest: Mapped[Optional["Pest"]] = relationship("Pest")


class PestDamageRecord(Base):
    """Damage characteristics recorded during pest infestation."""
    __tablename__ = "pest_damage_records"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    pest_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plant_observation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("plant_observations.id", ondelete="SET NULL"),
        nullable=True,
    )
    damage_type: Mapped[str] = mapped_column(String(50), nullable=False)
    affected_area_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    severity_index: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "damage_type IN ('defoliation', 'stem_boring', 'leaf_curling', 'fruit_piercing', 'root_galling', 'sap_depletion', 'gall_formation')",
            name="chk_pest_damage_type",
        ),
        CheckConstraint(
            "severity_index >= 1 AND severity_index <= 5",
            name="chk_pest_damage_severity_idx",
        ),
        CheckConstraint(
            "affected_area_percentage IS NULL OR (affected_area_percentage >= 0 AND affected_area_percentage <= 100)",
            name="chk_pest_damage_pct_bounds",
        ),
    )

    pest: Mapped["Pest"] = relationship("Pest", back_populates="damage_records")
    observation: Mapped[Optional["PlantObservation"]] = relationship("PlantObservation")


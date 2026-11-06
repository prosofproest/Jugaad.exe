"""
CropSentinel AI — Domain 7: Pest Management Database
Tables:
- ipm_methods
- pest_control_options
- biological_controls
- mechanical_controls
- cultural_controls
- physical_controls
- behavioral_controls
- chemical_controls
- pesticide_registrations
- treatment_records
- treatment_effectiveness

COMPLIANCE:
Supports crop-specific applicability, statutory approval status, registration numbers,
validity periods, and treatment history. Strictly NO fabricated pesticide data.
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
    TimestampMixin,
)


class IPMMethod(Base, TimestampMixin):
    """Integrated Pest Management (IPM) foundational methodology."""
    __tablename__ = "ipm_methods"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    environmental_impact_rating: Mapped[str] = mapped_column(String(20), default="low", nullable=False)

    __table_args__ = (
        CheckConstraint(
            "category IN ('preventive', 'cultural', 'mechanical', 'physical', 'biological', 'behavioral', 'chemical')",
            name="chk_ipm_methods_category",
        ),
        CheckConstraint(
            "environmental_impact_rating IN ('none', 'low', 'moderate', 'high', 'severe')",
            name="chk_ipm_methods_env_impact",
        ),
    )

    control_options: Mapped[List["PestControlOption"]] = relationship("PestControlOption", back_populates="ipm_method")


class PestControlOption(Base, TimestampMixin):
    """Specific control strategy options mapped to pests, diseases, and crops."""
    __tablename__ = "pest_control_options"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    pest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    disease_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("diseases.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    crop_type_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("crop_types.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    ipm_method_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ipm_methods.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    strategy_summary: Mapped[str] = mapped_column(Text, nullable=False)
    applicability_window: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    effectiveness_rating: Mapped[str] = mapped_column(String(20), default="moderate", nullable=False)

    __table_args__ = (
        CheckConstraint(
            "pest_id IS NOT NULL OR disease_id IS NOT NULL",
            name="chk_control_options_target_present",
        ),
        CheckConstraint(
            "effectiveness_rating IN ('low', 'moderate', 'high', 'very_high')",
            name="chk_control_options_eff_rating",
        ),
    )

    pest: Mapped[Optional["Pest"]] = relationship("Pest")
    disease: Mapped[Optional["Disease"]] = relationship("Disease")
    crop_type: Mapped[Optional["CropType"]] = relationship("CropType")
    ipm_method: Mapped["IPMMethod"] = relationship("IPMMethod", back_populates="control_options")


class BiologicalControl(Base, TimestampMixin):
    """Natural enemies, parasitoids, entomopathogens, and bio-agents."""
    __tablename__ = "biological_controls"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    ipm_method_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ipm_methods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[str] = mapped_column(String(150), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_pest_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    release_rate: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    optimal_timing: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    conservation_practices: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "agent_type IN ('predator', 'parasitoid', 'pathogen', 'entomopathogen', 'microbial', 'antagonist')",
            name="chk_biocontrol_agent_type",
        ),
    )

    ipm_method: Mapped["IPMMethod"] = relationship("IPMMethod")
    target_pest: Mapped["Pest"] = relationship("Pest")


class MechanicalControl(Base, TimestampMixin):
    """Mechanical interventions (hand picking, mechanical shaking, tillage, suction)."""
    __tablename__ = "mechanical_controls"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    ipm_method_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ipm_methods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    method_name: Mapped[str] = mapped_column(String(150), nullable=False)
    equipment_needed: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    labor_intensity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    execution_steps: Mapped[Text] = mapped_column(Text, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "labor_intensity IN ('low', 'medium', 'high', 'intensive')",
            name="chk_mech_control_labor",
        ),
    )

    ipm_method: Mapped["IPMMethod"] = relationship("IPMMethod")


class CulturalControl(Base, TimestampMixin):
    """Agronomic and cultural practices (crop rotation, intercropping, field sanitation)."""
    __tablename__ = "cultural_controls"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    ipm_method_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ipm_methods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    practice_type: Mapped[str] = mapped_column(String(50), nullable=False)
    implementation_protocol: Mapped[Text] = mapped_column(Text, nullable=False)
    recommended_timing: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "practice_type IN ('crop_rotation', 'intercropping', 'trap_cropping', 'field_sanitation', 'adjusted_sowing', 'resistant_varieties')",
            name="chk_cult_control_practice",
        ),
    )

    ipm_method: Mapped["IPMMethod"] = relationship("IPMMethod")


class PhysicalControl(Base, TimestampMixin):
    """Physical barriers and physical methods (heat treatment, solarization, row covers, nets)."""
    __tablename__ = "physical_controls"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    ipm_method_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ipm_methods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    control_mechanism: Mapped[str] = mapped_column(String(50), nullable=False)
    technical_parameters: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    installation_guide: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "control_mechanism IN ('solarization', 'soil_steaming', 'mesh_exclusion', 'row_covers', 'reflective_mulch', 'flame_weeding')",
            name="chk_phys_control_mechanism",
        ),
    )

    ipm_method: Mapped["IPMMethod"] = relationship("IPMMethod")


class BehavioralControl(Base, TimestampMixin):
    """Behavioral manipulation methods (pheromone traps, light traps, sticky boards, visual decoys)."""
    __tablename__ = "behavioral_controls"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    ipm_method_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ipm_methods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attractant_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trap_density_per_hectare: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    replacement_interval_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    monitoring_threshold: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "attractant_type IN ('sex_pheromone', 'aggregation_pheromone', 'yellow_sticky_trap', 'blue_sticky_trap', 'light_trap', 'food_bait')",
            name="chk_behav_control_attractant",
        ),
    )

    ipm_method: Mapped["IPMMethod"] = relationship("IPMMethod")


class ChemicalControl(Base, TimestampMixin):
    """Officially registered active ingredients and chemical formulations."""
    __tablename__ = "chemical_controls"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    ipm_method_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ipm_methods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    active_ingredient: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    chemical_class: Mapped[str] = mapped_column(String(100), nullable=False)
    mode_of_action: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    resistance_risk_group: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    toxicity_class: Mapped[str] = mapped_column(String(20), nullable=False)
    phi_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rei_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "toxicity_class IN ('WHO_Ia', 'WHO_Ib', 'WHO_II', 'WHO_III', 'WHO_U', 'Green_Triangle', 'Blue_Triangle', 'Yellow_Triangle', 'Red_Triangle')",
            name="chk_chem_control_toxicity",
        ),
        CheckConstraint("phi_days IS NULL OR phi_days >= 0", name="chk_chem_phi_nonneg"),
        CheckConstraint("rei_hours IS NULL OR rei_hours >= 0", name="chk_chem_rei_nonneg"),
    )

    ipm_method: Mapped["IPMMethod"] = relationship("IPMMethod")
    registrations: Mapped[List["PesticideRegistration"]] = relationship(
        "PesticideRegistration", back_populates="chemical_control", cascade="all, delete-orphan"
    )


class PesticideRegistration(Base, TimestampMixin):
    """Official legal pesticide registrations (e.g. CIBRC / EPA approvals)."""
    __tablename__ = "pesticide_registrations"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    chemical_control_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("chemical_controls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    registration_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    registering_authority: Mapped[str] = mapped_column(String(100), default="CIBRC", nullable=False)
    registered_trade_name: Mapped[str] = mapped_column(String(150), nullable=False)
    approved_crop_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("crop_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    approved_pest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    approved_dosage_per_ha: Mapped[str] = mapped_column(String(100), nullable=False)
    approval_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'provisional', 'expired', 'restricted', 'banned', 'cancelled')",
            name="chk_pesticide_reg_status",
        ),
    )

    chemical_control: Mapped["ChemicalControl"] = relationship("ChemicalControl", back_populates="registrations")
    approved_crop: Mapped["CropType"] = relationship("CropType")
    approved_pest: Mapped[Optional["Pest"]] = relationship("Pest")


class TreatmentRecord(Base, TimestampMixin):
    """Record of pest management treatments applied to a farm plot."""
    __tablename__ = "treatment_records"

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
    applied_by: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    ipm_method_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ipm_methods.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    chemical_control_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("chemical_controls.id", ondelete="SET NULL"),
        nullable=True,
    )
    registration_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pesticide_registrations.id", ondelete="SET NULL"),
        nullable=True,
    )
    application_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dosage_applied: Mapped[str] = mapped_column(String(100), nullable=False)
    weather_conditions_at_spray: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    safety_equipment_used: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    plot: Mapped["FarmPlot"] = relationship("FarmPlot")
    crop_instance: Mapped["CropInstance"] = relationship("CropInstance")
    applicator: Mapped["User"] = relationship("User")
    ipm_method: Mapped["IPMMethod"] = relationship("IPMMethod")
    chemical_control: Mapped[Optional["ChemicalControl"]] = relationship("ChemicalControl")
    registration: Mapped[Optional["PesticideRegistration"]] = relationship("PesticideRegistration")
    effectiveness_evaluations: Mapped[List["TreatmentEffectiveness"]] = relationship(
        "TreatmentEffectiveness", back_populates="treatment_record", cascade="all, delete-orphan"
    )


class TreatmentEffectiveness(Base):
    """Post-treatment verification and outcomes."""
    __tablename__ = "treatment_effectiveness"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    treatment_record_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("treatment_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evaluation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    days_post_treatment: Mapped[int] = mapped_column(Integer, nullable=False)
    pest_mortality_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    crop_recovery_score: Mapped[int] = mapped_column(Integer, nullable=False)
    phytotoxicity_observed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evaluator_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    evaluation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("days_post_treatment >= 0", name="chk_treat_eff_days_nonneg"),
        CheckConstraint(
            "pest_mortality_percentage IS NULL OR (pest_mortality_percentage >= 0 AND pest_mortality_percentage <= 100)",
            name="chk_treat_eff_mortality_range",
        ),
        CheckConstraint(
            "crop_recovery_score >= 1 AND crop_recovery_score <= 5",
            name="chk_treat_eff_recovery_score",
        ),
    )

    treatment_record: Mapped["TreatmentRecord"] = relationship("TreatmentRecord", back_populates="effectiveness_evaluations")
    evaluator: Mapped["User"] = relationship("User")


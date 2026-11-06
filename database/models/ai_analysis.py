"""
CropSentinel AI — Domain 6: AI Analysis Database
Tables:
- ai_model_versions
- ai_analysis
- ai_predictions
- ai_detections
- ai_confidence
- diagnosis_records
- ai_feedback

TRACEABILITY ARCHITECTURE:
AI Analysis -> AI Model Version -> AI Prediction -> AI Detection -> Diagnosis Record -> AI Feedback
Predictions are strictly append-only; predictions are never silently overwritten.
Confidence scores are strictly bounded numeric types [0.0000, 1.0000].
Expert diagnoses are kept rigorously distinct from AI predictions.
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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from database.models.base import (
    Base,
    PortableUUID,
    TimestampMixin,
)


class AIModelVersion(Base, TimestampMixin):
    """Registered AI/ML model versions deployed for field inference."""
    __tablename__ = "ai_model_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    version_tag: Mapped[str] = mapped_column(String(50), nullable=False)
    model_family: Mapped[str] = mapped_column(String(50), nullable=False)
    weights_digest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    training_dataset_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    f1_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    inference_runtime: Mapped[str] = mapped_column(String(50), default="onnxruntime", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("model_name", "version_tag", name="uq_ai_model_name_version"),
        CheckConstraint(
            "model_family IN ('yolo', 'resnet', 'efficientnet', 'vit', 'ensemble', 'custom')",
            name="chk_ai_model_family",
        ),
    )

    predictions: Mapped[List["AIPrediction"]] = relationship("AIPrediction", back_populates="model_version")


class AIAnalysis(Base, TimestampMixin):
    """Analysis request lifecycle linking media to inference pipelines."""
    __tablename__ = "ai_analysis"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    media_file_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("media_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(50), default="detection", nullable=False)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'quarantined')",
            name="chk_ai_analysis_status",
        ),
        CheckConstraint(
            "analysis_type IN ('detection', 'classification', 'segmentation', 'severity_estimation', 'multitask')",
            name="chk_ai_analysis_type",
        ),
    )

    media_file: Mapped["MediaFile"] = relationship("MediaFile")
    requester: Mapped["User"] = relationship("User")
    predictions: Mapped[List["AIPrediction"]] = relationship(
        "AIPrediction", back_populates="analysis", cascade="all, delete-orphan"
    )
    diagnosis_record: Mapped[Optional["DiagnosisRecord"]] = relationship(
        "DiagnosisRecord", back_populates="analysis", uselist=False
    )


class AIPrediction(Base):
    """
    Inference prediction output from AI models.
    Append-only: past predictions are marked is_superseded, never deleted or overwritten.
    """
    __tablename__ = "ai_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ai_analysis.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ai_model_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
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
    primary_diagnosis: Mapped[str] = mapped_column(String(150), nullable=False)
    confidence_score: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=False,
    )
    severity_level: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    inference_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    is_superseded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0.0000 AND confidence_score <= 1.0000",
            name="chk_ai_pred_confidence_range",
        ),
        CheckConstraint(
            "severity_level IN ('none', 'low', 'medium', 'high', 'severe')",
            name="chk_ai_pred_severity_level",
        ),
    )

    analysis: Mapped["AIAnalysis"] = relationship("AIAnalysis", back_populates="predictions")
    model_version: Mapped["AIModelVersion"] = relationship("AIModelVersion", back_populates="predictions")
    pest: Mapped[Optional["Pest"]] = relationship("Pest")
    disease: Mapped[Optional["Disease"]] = relationship("Disease")
    detections: Mapped[List["AIDetection"]] = relationship(
        "AIDetection", back_populates="prediction", cascade="all, delete-orphan"
    )
    confidences: Mapped[List["AIConfidence"]] = relationship(
        "AIConfidence", back_populates="prediction", cascade="all, delete-orphan"
    )


class AIDetection(Base):
    """Bounding box, mask, and localized symptom detection."""
    __tablename__ = "ai_detections"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ai_predictions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    bbox_x_min: Mapped[float] = mapped_column(Numeric(precision=6, scale=4), nullable=False)
    bbox_y_min: Mapped[float] = mapped_column(Numeric(precision=6, scale=4), nullable=False)
    bbox_x_max: Mapped[float] = mapped_column(Numeric(precision=6, scale=4), nullable=False)
    bbox_y_max: Mapped[float] = mapped_column(Numeric(precision=6, scale=4), nullable=False)
    detection_confidence: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=False,
    )
    mask_rle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "detection_confidence >= 0.0000 AND detection_confidence <= 1.0000",
            name="chk_ai_detection_confidence_range",
        ),
        CheckConstraint("bbox_x_min >= 0 AND bbox_x_min <= bbox_x_max", name="chk_ai_det_box_x"),
        CheckConstraint("bbox_y_min >= 0 AND bbox_y_min <= bbox_y_max", name="chk_ai_det_box_y"),
    )

    prediction: Mapped["AIPrediction"] = relationship("AIPrediction", back_populates="detections")


class AIConfidence(Base):
    """Detailed calibration, entropy, and multi-class probability distribution."""
    __tablename__ = "ai_confidence"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ai_predictions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_label: Mapped[str] = mapped_column(String(100), nullable=False)
    probability: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=False,
    )
    calibration_method: Mapped[str] = mapped_column(String(50), default="platt", nullable=False)
    entropy_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "probability >= 0.0000 AND probability <= 1.0000",
            name="chk_ai_conf_probability_range",
        ),
    )

    prediction: Mapped["AIPrediction"] = relationship("AIPrediction", back_populates="confidences")


class DiagnosisRecord(Base, TimestampMixin):
    """
    Final authoritative diagnosis record.
    Rigorously distinguishes expert human verification from pure AI predictions.
    """
    __tablename__ = "diagnosis_records"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ai_analysis.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prediction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("ai_predictions.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_by: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    confirmed_pest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_disease_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("diseases.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmation_status: Mapped[str] = mapped_column(String(50), nullable=False)
    expert_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    diagnosed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "confirmation_status IN ('expert_confirmed', 'expert_rejected', 'pending_review', 'auto_accepted')",
            name="chk_diag_confirmation_status",
        ),
    )

    analysis: Mapped["AIAnalysis"] = relationship("AIAnalysis", back_populates="diagnosis_record")
    prediction: Mapped[Optional["AIPrediction"]] = relationship("AIPrediction")
    verifier: Mapped["User"] = relationship("User")
    confirmed_pest: Mapped[Optional["Pest"]] = relationship("Pest")
    confirmed_disease: Mapped[Optional["Disease"]] = relationship("Disease")
    feedbacks: Mapped[List["AIFeedback"]] = relationship(
        "AIFeedback", back_populates="diagnosis_record", cascade="all, delete-orphan"
    )


class AIFeedback(Base):
    """User and expert ground-truth corrections and feedback on model predictions."""
    __tablename__ = "ai_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    diagnosis_record_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("diagnosis_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ai_predictions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)
    corrected_pest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("pests.id", ondelete="SET NULL"),
        nullable=True,
    )
    corrected_disease_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("diseases.id", ondelete="SET NULL"),
        nullable=True,
    )
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "feedback_type IN ('agree', 'disagree', 'false_positive', 'missed_detection', 'unclear_image')",
            name="chk_ai_feedback_type",
        ),
    )

    diagnosis_record: Mapped["DiagnosisRecord"] = relationship("DiagnosisRecord", back_populates="feedbacks")
    prediction: Mapped["AIPrediction"] = relationship("AIPrediction")
    user: Mapped["User"] = relationship("User")


"""
CropSentinel AI — Domain 4: Media Database
Tables:
- media_files
- media_frames
- media_observations
- media_locations
- media_analysis_links

CRITICAL COMPLIANCE:
PostgreSQL stores ONLY metadata and object storage references (S3/GCS keys).
Raw binary images and videos are NEVER stored as BLOBs in PostgreSQL.
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
    PostGISGeometry,
    TimestampMixin,
)


class MediaFile(Base, TimestampMixin):
    """
    Metadata and object storage reference for captured images and videos.
    Strictly NO raw binary BLOB storage.
    """
    __tablename__ = "media_files"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    storage_provider: Mapped[str] = mapped_column(String(50), default="s3", nullable=False)
    bucket_name: Mapped[str] = mapped_column(String(100), nullable=False)
    object_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    width_px: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height_px: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    capture_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    upload_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    is_quarantined: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quarantine_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        CheckConstraint("media_type IN ('image', 'video')", name="chk_media_files_media_type"),
        CheckConstraint("file_size_bytes > 0", name="chk_media_files_positive_size"),
        CheckConstraint(
            "mime_type IN ('image/jpeg', 'image/png', 'image/webp', 'video/mp4', 'video/quicktime')",
            name="chk_media_files_mime_type",
        ),
    )

    uploader: Mapped["User"] = relationship("User")
    frames: Mapped[List["MediaFrame"]] = relationship(
        "MediaFrame", back_populates="media_file", cascade="all, delete-orphan"
    )
    media_location: Mapped[Optional["MediaLocation"]] = relationship(
        "MediaLocation", back_populates="media_file", uselist=False, cascade="all, delete-orphan"
    )
    observations: Mapped[List["MediaObservation"]] = relationship(
        "MediaObservation", back_populates="media_file", cascade="all, delete-orphan"
    )
    analysis_links: Mapped[List["MediaAnalysisLink"]] = relationship(
        "MediaAnalysisLink", back_populates="media_file", cascade="all, delete-orphan"
    )


class MediaFrame(Base):
    """Extracted video frame metadata."""
    __tablename__ = "media_frames"

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
    frame_number: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp_offset_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    frame_object_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    width_px: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height_px: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("media_file_id", "frame_number", name="uq_media_frames_file_num"),
        CheckConstraint("frame_number >= 0", name="chk_media_frames_num_nonneg"),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 1.0)", name="chk_media_frames_quality"),
    )

    media_file: Mapped["MediaFile"] = relationship("MediaFile", back_populates="frames")


class MediaObservation(Base):
    """Junction linking media files to plant observations."""
    __tablename__ = "media_observations"

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
    observation_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("plant_observations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    media_role: Mapped[str] = mapped_column(String(50), default="symptom_closeup", nullable=False)
    attached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("media_file_id", "observation_id", name="uq_media_obs_pair"),
        CheckConstraint(
            "media_role IN ('primary', 'symptom_closeup', 'whole_plant', 'field_overview', 'underside_leaf', 'stem_cross_section')",
            name="chk_media_obs_role",
        ),
    )

    media_file: Mapped["MediaFile"] = relationship("MediaFile", back_populates="observations")
    observation: Mapped["PlantObservation"] = relationship("PlantObservation")


class MediaLocation(Base):
    """Geographical GPS metadata captured with media files."""
    __tablename__ = "media_locations"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    media_file_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("media_files.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    location: Mapped[str] = mapped_column(
        PostGISGeometry("POINT", 4326),
        nullable=False,
    )
    altitude_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gps_accuracy_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    heading_degrees: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_media_locations_geom", "location", postgresql_using="gist"),
    )

    media_file: Mapped["MediaFile"] = relationship("MediaFile", back_populates="media_location")


class MediaAnalysisLink(Base):
    """Link between media assets (or specific frames) and AI analysis pipelines."""
    __tablename__ = "media_analysis_links"

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
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("ai_analysis.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    frame_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("media_frames.id", ondelete="SET NULL"),
        nullable=True,
    )
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    media_file: Mapped["MediaFile"] = relationship("MediaFile", back_populates="analysis_links")


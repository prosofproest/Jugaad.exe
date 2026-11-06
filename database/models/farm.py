"""
CropSentinel AI — Domain 2: Farm Database
Tables:
- farms
- farm_boundaries
- farm_sections
- farm_plots
- farm_locations
- farm_members
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
    SoftDeleteMixin,
    TimestampMixin,
)


class Farm(Base, TimestampMixin, SoftDeleteMixin):
    """Primary farm record."""
    __tablename__ = "farms"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    registration_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    total_area_sqm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'archived')", name="chk_farms_status"),
        CheckConstraint("total_area_sqm IS NULL OR total_area_sqm > 0", name="chk_farms_positive_area"),
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])
    boundaries: Mapped[List["FarmBoundary"]] = relationship(
        "FarmBoundary", back_populates="farm", cascade="all, delete-orphan"
    )
    sections: Mapped[List["FarmSection"]] = relationship(
        "FarmSection", back_populates="farm", cascade="all, delete-orphan"
    )
    plots: Mapped[List["FarmPlot"]] = relationship(
        "FarmPlot", back_populates="farm", cascade="all, delete-orphan"
    )
    locations: Mapped[List["FarmLocation"]] = relationship(
        "FarmLocation", back_populates="farm", cascade="all, delete-orphan"
    )
    members: Mapped[List["FarmMember"]] = relationship(
        "FarmMember", back_populates="farm", cascade="all, delete-orphan"
    )


class FarmBoundary(Base):
    """Authoritative GPS boundaries of the farm."""
    __tablename__ = "farm_boundaries"

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
    boundary_polygon: Mapped[str] = mapped_column(
        PostGISGeometry("MULTIPOLYGON", 4326),
        nullable=False,
    )
    perimeter_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    area_sqm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    elevation_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_farm_boundaries_geom", "boundary_polygon", postgresql_using="gist"),
    )

    farm: Mapped["Farm"] = relationship("Farm", back_populates="boundaries")


class FarmSection(Base, TimestampMixin):
    """Divided agricultural management section within a farm."""
    __tablename__ = "farm_sections"

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
    section_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    section_polygon: Mapped[Optional[str]] = mapped_column(
        PostGISGeometry("POLYGON", 4326),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("farm_id", "section_code", name="uq_farm_section_code"),
        Index("idx_farm_sections_geom", "section_polygon", postgresql_using="gist"),
    )

    farm: Mapped["Farm"] = relationship("Farm", back_populates="sections")
    plots: Mapped[List["FarmPlot"]] = relationship(
        "FarmPlot", back_populates="section", cascade="all, delete-orphan"
    )


class FarmPlot(Base, TimestampMixin):
    """
    Independently identifiable agricultural plot inside a section or farm.
    Updating the crop or boundary of one plot never affects or overwrites another.
    """
    __tablename__ = "farm_plots"

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
    section_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("farm_sections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    plot_code: Mapped[str] = mapped_column(String(50), nullable=False)
    soil_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    irrigation_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    area_sqm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    plot_polygon: Mapped[Optional[str]] = mapped_column(
        PostGISGeometry("POLYGON", 4326),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("farm_id", "plot_code", name="uq_farm_plot_code"),
        CheckConstraint("area_sqm IS NULL OR area_sqm > 0", name="chk_farm_plots_positive_area"),
        Index("idx_farm_plots_geom", "plot_polygon", postgresql_using="gist"),
    )

    farm: Mapped["Farm"] = relationship("Farm", back_populates="plots")
    section: Mapped[Optional["FarmSection"]] = relationship("FarmSection", back_populates="plots")


class FarmLocation(Base):
    """Postal and geographic address record for a farm."""
    __tablename__ = "farm_locations"

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
    address_line: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    village_or_town: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    taluk_or_subdistrict: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), default="India", nullable=False)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    centroid: Mapped[str] = mapped_column(
        PostGISGeometry("POINT", 4326),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_farm_locations_centroid", "centroid", postgresql_using="gist"),
    )

    farm: Mapped["Farm"] = relationship("Farm", back_populates="locations")


class FarmMember(Base):
    """Access permissions linking users to farms."""
    __tablename__ = "farm_members"

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
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    access_level: Mapped[str] = mapped_column(String(30), default="viewer", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("farm_id", "user_id", name="uq_farm_members_farm_user"),
        CheckConstraint(
            "access_level IN ('owner', 'manager', 'agronomist', 'worker', 'viewer')",
            name="chk_farm_members_access_level",
        ),
    )

    farm: Mapped["Farm"] = relationship("Farm", back_populates="members")
    user: Mapped["User"] = relationship("User")


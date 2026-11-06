"""
CropSentinel AI — Domain 1: User Database
Tables:
- users
- user_roles
- user_profiles
- user_permissions
- user_sessions
- user_preferences
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, PortableUUID, SoftDeleteMixin, TimestampMixin


class User(Base, TimestampMixin, SoftDeleteMixin):
    """Primary user account table."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), unique=True, nullable=True, index=True)
    phone_e164: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended', 'pending_verification')",
            name="chk_users_status",
        ),
        CheckConstraint(
            "email IS NOT NULL OR phone_e164 IS NOT NULL",
            name="chk_users_contact_present",
        ),
    )

    # Relationships
    roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        primaryjoin="User.id == UserRole.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    profile: Mapped[Optional["UserProfile"]] = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    permissions: Mapped[List["UserPermission"]] = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    preference: Mapped[Optional["UserPreference"]] = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserRole(Base):
    """User assigned roles (farmer, expert, agent, admin, agronomist, pathologist, etc.)."""
    __tablename__ = "user_roles"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    granted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "role", name="uq_user_roles_user_role"),
        CheckConstraint(
            "role IN ('farmer', 'expert', 'agent', 'admin', 'pathologist', 'agronomist', 'extension_worker', 'researcher')",
            name="chk_user_roles_valid",
        ),
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="roles")


class UserProfile(Base, TimestampMixin):
    """User profile information (1-to-1 with User)."""
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_contact_method: Mapped[str] = mapped_column(String(20), default="phone", nullable=False)

    __table_args__ = (
        CheckConstraint(
            "preferred_contact_method IN ('phone', 'sms', 'email', 'in_app')",
            name="chk_user_profiles_contact_method",
        ),
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")


class UserPermission(Base):
    """Granular permissions granted to users."""
    __tablename__ = "user_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_code: Mapped[str] = mapped_column(String(100), nullable=False)
    scope: Mapped[str] = mapped_column(String(100), default="global", nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "permission_code", "scope", name="uq_user_permission_scope"),
    )

    user: Mapped["User"] = relationship("User", back_populates="permissions")


class UserSession(Base):
    """User authentication and active session information."""
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="sessions")


class UserPreference(Base, TimestampMixin):
    """User preferences, UI language, settings (1-to-1 with User)."""
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    preferred_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata", nullable=False)
    theme: Mapped[str] = mapped_column(String(20), default="system", nullable=False)
    notification_frequency: Mapped[str] = mapped_column(String(20), default="instant", nullable=False)

    __table_args__ = (
        CheckConstraint(
            "notification_frequency IN ('instant', 'daily_digest', 'weekly', 'muted')",
            name="chk_user_preferences_notif_freq",
        ),
    )

    user: Mapped["User"] = relationship("User", back_populates="preference")

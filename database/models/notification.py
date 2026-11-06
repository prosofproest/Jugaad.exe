"""
CropSentinel AI — Domain 11: Notification Database
Tables:
- notifications
- alert_rules
- user_alert_preferences
- scheduled_tasks
- sync_logs
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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from database.models.base import (
    Base,
    PortableUUID,
    TimestampMixin,
)


class Notification(Base):
    """Dispatched system, alert, and advisory notifications."""
    __tablename__ = "notifications"

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
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="push", nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('pest_alert', 'weather_warning', 'advisory_update', 'inspection_reminder', 'system', 'treatment_due')",
            name="chk_notif_type",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'critical')",
            name="chk_notif_priority",
        ),
        CheckConstraint(
            "status IN ('pending', 'sent', 'delivered', 'read', 'failed')",
            name="chk_notif_status",
        ),
        CheckConstraint(
            "channel IN ('push', 'sms', 'in_app', 'email', 'voice_call')",
            name="chk_notif_channel",
        ),
        CheckConstraint("retry_count >= 0", name="chk_notif_retry_nonneg"),
    )

    user: Mapped["User"] = relationship("User")


class AlertRule(Base, TimestampMixin):
    """Dynamic automated alerting criteria and threshold conditions."""
    __tablename__ = "alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    rule_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    condition_expression: Mapped[str] = mapped_column(Text, nullable=False)
    threshold_value: Mapped[Optional[float]] = mapped_column(Numeric(precision=8, scale=4), nullable=True)
    target_role: Mapped[str] = mapped_column(String(50), default="farmer", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    creator: Mapped["User"] = relationship("User")


class UserAlertPreference(Base, TimestampMixin):
    """User-specific alert thresholds, channels, and quiet hour settings."""
    __tablename__ = "user_alert_preferences"

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
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # e.g. "22:00"
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)    # e.g. "06:00"
    min_priority_threshold: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)

    __table_args__ = (
        CheckConstraint(
            "min_priority_threshold IN ('low', 'medium', 'high', 'critical')",
            name="chk_user_alert_min_priority",
        ),
    )

    user: Mapped["User"] = relationship("User")


class ScheduledTask(Base):
    """Asynchronous and scheduled agricultural tasks and reminder queues."""
    __tablename__ = "scheduled_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    task_name: Mapped[str] = mapped_column(String(100), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recurrence_pattern: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "task_type IN ('scouting_reminder', 'treatment_followup', 'sensor_sync', 'weekly_digest', 'weather_alert')",
            name="chk_task_type_valid",
        ),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="chk_task_status_valid",
        ),
        CheckConstraint("retry_count >= 0", name="chk_task_retry_nonneg"),
    )

    target_user: Mapped[Optional["User"]] = relationship("User")


class SyncLog(Base):
    """Audit log of mobile edge device offline data synchronizations."""
    __tablename__ = "sync_logs"

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
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sync_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    client_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    server_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    records_synced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sync_status: Mapped[str] = mapped_column(String(30), default="success", nullable=False)
    conflict_resolution_strategy: Mapped[str] = mapped_column(String(50), default="server_wins", nullable=False)
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "sync_status IN ('success', 'partial_failure', 'conflict', 'failed')",
            name="chk_sync_status_valid",
        ),
        CheckConstraint("records_synced >= 0", name="chk_sync_records_nonneg"),
    )

    user: Mapped["User"] = relationship("User")


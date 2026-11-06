"""Video reading persistence: stored clips and append-only readings.

Revision ID: 0003_video_persistence
Revises: 0002_chat_persistence
Create Date: 2026-11-06

Additive only. The video bytes stay outside the database (``APP_MEDIA_ROOT``);
this migration stores only metadata, the relative storage path and the reading.
``downgrade()`` drops ``video_readings`` before ``video_uploads``; the chat
tables from ``0002_chat_persistence`` are untouched.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_video_persistence"
down_revision: str | None = "0002_chat_persistence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "video_uploads",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("fps", sa.Float(), nullable=False),
        sa.Column("frame_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_video_uploads"),
    )
    op.create_index("ix_video_uploads_owner_id", "video_uploads", ["owner_id"])
    op.create_index("ix_video_uploads_sha256", "video_uploads", ["sha256"])

    op.create_table(
        "video_readings",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("video_id", sa.String(length=64), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("frames", sa.JSON(), nullable=True),
        sa.Column("engine_version", sa.String(length=120), nullable=False),
        sa.Column("detector_version", sa.String(length=80), nullable=False),
        sa.Column("tracker_version", sa.String(length=80), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("calibrated", sa.Boolean(), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["video_uploads.id"],
            name="fk_video_readings_video_id_video_uploads",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_video_readings"),
    )
    op.create_index("ix_video_readings_video_id", "video_readings", ["video_id"])
    op.create_index("ix_video_readings_owner_id", "video_readings", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_video_readings_owner_id", table_name="video_readings")
    op.drop_index("ix_video_readings_video_id", table_name="video_readings")
    op.drop_table("video_readings")

    op.drop_index("ix_video_uploads_sha256", table_name="video_uploads")
    op.drop_index("ix_video_uploads_owner_id", table_name="video_uploads")
    op.drop_table("video_uploads")

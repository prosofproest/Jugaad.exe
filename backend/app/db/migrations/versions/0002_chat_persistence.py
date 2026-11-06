"""Chat persistence: conversations, messages, uploads and review requests.

Revision ID: 0002_chat_persistence
Revises: 0001_baseline
Create Date: 2026-11-06

Additive only. Every table is new; downgrade drops them in reverse dependency
order so a rollback leaves the baseline intact. The image bytes themselves live
outside the database (``APP_MEDIA_ROOT``); this migration stores only metadata
and the relative storage path.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_chat_persistence"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_conversations"),
    )
    op.create_index("ix_conversations_owner_id", "conversations", ["owner_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("client_message_id", sa.String(length=128), nullable=True),
        sa.Column("turn_id", sa.String(length=128), nullable=True),
        sa.Column("observation_id", sa.String(length=64), nullable=True),
        sa.Column("assessment", sa.JSON(), nullable=True),
        sa.Column("image", sa.JSON(), nullable=True),
        sa.Column("next_steps", sa.JSON(), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name="fk_messages_conversation_id_conversations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_messages"),
        sa.UniqueConstraint(
            "conversation_id",
            "client_message_id",
            name="uq_messages_conversation_client",
        ),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_turn_id", "messages", ["turn_id"])

    op.create_table(
        "message_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=False),
        sa.Column("message_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=48), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name="fk_message_events_conversation_id_conversations",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["messages.id"],
            name="fk_message_events_message_id_messages",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_message_events"),
    )
    op.create_index("ix_message_events_conversation_id", "message_events", ["conversation_id"])
    op.create_index("ix_message_events_message_id", "message_events", ["message_id"])

    op.create_table(
        "image_uploads",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("laplacian_variance", sa.Float(), nullable=False),
        sa.Column("mean_luma", sa.Float(), nullable=False),
        sa.Column("clipped_fraction", sa.Float(), nullable=False),
        sa.Column("plant_presence", sa.Float(), nullable=False),
        sa.Column("quality_result", sa.String(length=32), nullable=False),
        sa.Column("quality_flags", sa.JSON(), nullable=True),
        sa.Column("quality_gate_version", sa.String(length=80), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_image_uploads"),
    )
    op.create_index("ix_image_uploads_owner_id", "image_uploads", ["owner_id"])
    op.create_index("ix_image_uploads_sha256", "image_uploads", ["sha256"])

    op.create_table(
        "review_requests",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=False),
        sa.Column("message_id", sa.String(length=64), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name="fk_review_requests_conversation_id_conversations",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["messages.id"],
            name="fk_review_requests_message_id_messages",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_review_requests"),
        sa.UniqueConstraint("message_id", name="uq_review_requests_message_id"),
    )
    op.create_index("ix_review_requests_conversation_id", "review_requests", ["conversation_id"])
    op.create_index("ix_review_requests_message_id", "review_requests", ["message_id"])
    op.create_index("ix_review_requests_owner_id", "review_requests", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_review_requests_owner_id", table_name="review_requests")
    op.drop_index("ix_review_requests_message_id", table_name="review_requests")
    op.drop_index("ix_review_requests_conversation_id", table_name="review_requests")
    op.drop_table("review_requests")

    op.drop_index("ix_image_uploads_sha256", table_name="image_uploads")
    op.drop_index("ix_image_uploads_owner_id", table_name="image_uploads")
    op.drop_table("image_uploads")

    op.drop_index("ix_message_events_message_id", table_name="message_events")
    op.drop_index("ix_message_events_conversation_id", table_name="message_events")
    op.drop_table("message_events")

    op.drop_index("ix_messages_turn_id", table_name="messages")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_conversations_owner_id", table_name="conversations")
    op.drop_table("conversations")

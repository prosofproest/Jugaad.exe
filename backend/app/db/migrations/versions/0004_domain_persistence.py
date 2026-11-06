"""Identity, domain, forecast, advisory, review and registry persistence.

Revision ID: 0004_domain_persistence
Revises: 0003_video_persistence
Create Date: 2026-11-06

Additive only. Creates the 43 tables not covered by 0002/0003 plus
the PostGIS extension. Tables are created in dependency order so every
foreign key references an earlier table. Downgrade drops the tables in
reverse dependency order and then drops the extension; the chat/video
tables from 0002/0003 are untouched. The extension DROP fails if any
non-ORM object depends on it — see MIGRATION_RECOVERY_GUIDE.md.

PostGIS note: the backend ORM declares no geometry columns (the pilot
API only serves block/mandal aggregates; geometry arrives when boundary
data is approved). The extension is still enabled so spatial columns
and GiST indexes can be added without a new extension migration. The
reference schema (``database/schema/01-schema.sql``) geometry is a
documented drift — it is not recreated here (see ORM_INVENTORY.md).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_domain_persistence"
down_revision: str | None = "0003_video_persistence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _is_postgresql() -> bool:
    """True only on PostgreSQL (SQLite dev/tests have no extensions)."""

    return op.get_bind().dialect.name == "postgresql"


def _enable_postgis() -> None:
    """Enable PostGIS on PostgreSQL, warning when unavailable.

    The ORM declares zero geometry columns, so the extension is inert
    for this schema and a missing extension must not block table
    creation. Production PostgreSQL MUST provide postgis (compose
    uses postgis/postgis:16-3.4); an isolated test database without it
    logs a warning and continues. PostGIS verification is then
    reported as blocked, never passed.

    The CREATE runs in a SAVEPOINT: a failed extension (missing control
    file) rolls back to the savepoint without aborting the migration
    transaction, so the 43 CREATE TABLEs that follow still execute.
    """

    if not _is_postgresql():
        return
    bind = op.get_bind()
    try:
        from alembic import context as _ctx

        _offline = _ctx.is_offline_mode()
    except Exception:  # noqa: BLE001
        _offline = False
    if _offline:
        # Buffered DDL only; never executes, so no abort is possible.
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        return
    try:
        with bind.begin_nested():
            bind.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS postgis")
    except Exception as exc:  # noqa: BLE001 - inert schema, warn only
        print(f"[0004] WARNING: postgis unavailable ({exc}); continuing without it.")


def upgrade() -> None:
    _enable_postgis()

    op.create_table(
        "advisories",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("crop_code", sa.String(length=60), nullable=False),
        sa.Column("target_code", sa.String(length=80), nullable=False),
        sa.Column("geo_scope", sa.JSON(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("current_version_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("withdrawal_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_advisories"),
    )
    op.create_index("ix_advisories_crop_code", "advisories", ["crop_code"])

    op.create_table(
        "alert_policies",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("geo_code", sa.String(length=64), nullable=False),
        sa.Column("target_code", sa.String(length=80), nullable=False),
        sa.Column("min_band", sa.String(length=30), nullable=False),
        sa.Column("min_coverage", sa.String(length=20), nullable=False),
        sa.Column("cooldown_hours", sa.Integer(), nullable=False),
        sa.Column("channels", sa.JSON(), nullable=False),
        sa.Column("approved_by", sa.String(length=64), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_alert_policies"),
    )
    op.create_index("ix_alert_policies_scope", "alert_policies", ["geo_code", "target_code"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=True),
        sa.Column("actor_role", sa.String(length=40), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=60), nullable=True),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_audit_events"),
    )
    op.create_index("ix_audit_entity", "audit_events", ["entity_type", "entity_id", "created_at"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])

    op.create_table(
        "crops",
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("supported", sa.Boolean(), nullable=False),
        sa.Column("supported_from", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("code", name="pk_crops"),
    )

    op.create_table(
        "feature_snapshots",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("crop_code", sa.String(length=60), nullable=False),
        sa.Column("target_code", sa.String(length=80), nullable=False),
        sa.Column("geo_code", sa.String(length=64), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("issue_time", sa.DateTime(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("source_refs", sa.JSON(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_feature_snapshots"),
    )

    op.create_table(
        "forecast_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("model_version", sa.String(length=80), nullable=True),
        sa.Column("areas_total", sa.Integer(), nullable=False),
        sa.Column("areas_scored", sa.Integer(), nullable=False),
        sa.Column("areas_insufficient", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_forecast_runs"),
    )

    op.create_table(
        "geographies",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("level", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("parent_code", sa.String(length=64), nullable=True),
        sa.Column("boundary_version", sa.String(length=60), nullable=False),
        sa.Column("valid_from", sa.DateTime(), nullable=True),
        sa.Column("valid_to", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("code", name="uq_geographies_code"),
        sa.PrimaryKeyConstraint("id", name="pk_geographies"),
    )

    op.create_table(
        "model_registry",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("version", sa.String(length=80), nullable=False),
        sa.Column("artefact_key", sa.String(length=400), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("approved_by", sa.String(length=64), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("kind", "version", name="uq_model_kind_version"),
        sa.PrimaryKeyConstraint("id", name="pk_model_registry"),
    )

    op.create_table(
        "otp_codes",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("phone_e164", sa.String(length=20), nullable=False),
        sa.Column("code_hash", sa.String(length=128), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_otp_codes"),
    )
    op.create_index("ix_otp_phone_created", "otp_codes", ["phone_e164", "created_at"])

    op.create_table(
        "roles",
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("code", name="pk_roles"),
    )

    op.create_table(
        "system_configs",
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("key", name="pk_system_configs"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("phone_e164", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("locale", sa.String(length=10), nullable=False),
        sa.Column("active_role", sa.String(length=40), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("mfa_secret", sa.String(length=64), nullable=True),
        sa.Column("failed_login_count", sa.Integer(), nullable=False),
        sa.Column("failed_login_first_at", sa.DateTime(), nullable=True),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("phone_e164", name="uq_users_phone_e164"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )

    op.create_table(
        "weather_snapshots",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("geo_code", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("source_timestamp", sa.DateTime(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("variables", sa.JSON(), nullable=False),
        sa.Column("completeness", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("is_stale", sa.Boolean(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_weather_snapshots"),
    )
    op.create_index("ix_weather_geo_source", "weather_snapshots", ["geo_code", "source_timestamp"])

    op.create_table(
        "advisory_versions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("advisory_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("body_md", sa.Text(), nullable=False),
        sa.Column("action_types", sa.JSON(), nullable=False),
        sa.Column("author_id", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=400), nullable=False),
        sa.Column("season", sa.String(length=40), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("valid_from", sa.DateTime(), nullable=False),
        sa.Column("valid_to", sa.DateTime(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["author_id"], ["users.id"], name="fk_advisory_versions_author_id_users"
        ),
        sa.ForeignKeyConstraint(
            ["advisory_id"], ["advisories.id"], name="fk_advisory_versions_advisory_id_advisories"
        ),
        sa.UniqueConstraint("advisory_id", "version", name="uq_advisory_version"),
        sa.PrimaryKeyConstraint("id", name="pk_advisory_versions"),
    )
    op.create_index("ix_advisory_versions_advisory_id", "advisory_versions", ["advisory_id"])

    op.create_table(
        "consents",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=60), nullable=False),
        sa.Column("version", sa.String(length=60), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("text_hash", sa.String(length=128), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_consents_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_consents"),
    )
    op.create_index("ix_consents_user_type", "consents", ["user_id", "type", "created_at"])

    op.create_table(
        "crop_calendars",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("crop_code", sa.String(length=60), nullable=False),
        sa.Column("geo_code", sa.String(length=64), nullable=False),
        sa.Column("season", sa.String(length=40), nullable=False),
        sa.Column("planting_window", sa.JSON(), nullable=False),
        sa.Column("stage_windows", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["crop_code"], ["crops.code"], name="fk_crop_calendars_crop_code_crops"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_crop_calendars"),
    )
    op.create_index(
        "ix_crop_calendars_lookup", "crop_calendars", ["crop_code", "geo_code", "season"]
    )

    op.create_table(
        "devices",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("platform", sa.String(length=30), nullable=False),
        sa.Column("app_version", sa.String(length=40), nullable=True),
        sa.Column("push_token", sa.String(length=255), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_devices_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_devices"),
    )
    op.create_index("ix_devices_user_id", "devices", ["user_id"])

    op.create_table(
        "export_jobs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("requested_by", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=400), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["requested_by"], ["users.id"], name="fk_export_jobs_requested_by_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_export_jobs"),
    )

    op.create_table(
        "forecasts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("crop_code", sa.String(length=60), nullable=False),
        sa.Column("target_code", sa.String(length=80), nullable=False),
        sa.Column("geo_code", sa.String(length=64), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("issue_time", sa.DateTime(), nullable=False),
        sa.Column("valid_from", sa.DateTime(), nullable=False),
        sa.Column("valid_to", sa.DateTime(), nullable=False),
        sa.Column("risk_band", sa.String(length=30), nullable=False),
        sa.Column("probability", sa.Numeric(precision=6, scale=5), nullable=True),
        sa.Column("confidence_band", sa.String(length=20), nullable=False),
        sa.Column("coverage", sa.String(length=20), nullable=False),
        sa.Column("coverage_detail", sa.JSON(), nullable=False),
        sa.Column("drivers", sa.JSON(), nullable=False),
        sa.Column("reason_code", sa.String(length=60), nullable=True),
        sa.Column("model_version", sa.String(length=80), nullable=False),
        sa.Column("feature_snapshot_id", sa.String(length=64), nullable=True),
        sa.Column("boundary_version", sa.String(length=60), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["feature_snapshot_id"],
            ["feature_snapshots.id"],
            name="fk_forecasts_feature_snapshot_id_feature_snapshots",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_forecasts"),
    )
    op.create_index(
        "ix_forecasts_lookup", "forecasts", ["crop_code", "target_code", "geo_code", "issue_time"]
    )

    op.create_table(
        "growing_areas",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("owner_user_id", sa.String(length=64), nullable=False),
        sa.Column("geo_code", sa.String(length=64), nullable=False),
        sa.Column("precision", sa.String(length=20), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_user_id"], ["users.id"], name="fk_growing_areas_owner_user_id_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_growing_areas"),
    )
    op.create_index("ix_growing_areas_geo_code", "growing_areas", ["geo_code"])
    op.create_index("ix_growing_areas_owner_user_id", "growing_areas", ["owner_user_id"])

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("scope", sa.String(length=80), nullable=False),
        sa.Column("key", sa.String(length=200), nullable=False),
        sa.Column("request_hash", sa.String(length=128), nullable=True),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_idempotency_records_user_id_users"
        ),
        sa.UniqueConstraint("user_id", "scope", "key", name="uq_idempotency_user_scope_key"),
        sa.PrimaryKeyConstraint("id", name="pk_idempotency_records"),
    )

    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("target_code", sa.String(length=80), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("quiet_start", sa.String(length=5), nullable=True),
        sa.Column("quiet_end", sa.String(length=5), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_notification_preferences_user_id_users"
        ),
        sa.UniqueConstraint("user_id", "channel", "target_code", name="uq_notification_pref"),
        sa.PrimaryKeyConstraint("id", name="pk_notification_preferences"),
    )
    op.create_index("ix_notification_preferences_user_id", "notification_preferences", ["user_id"])

    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("refresh_hash", sa.String(length=128), nullable=False),
        sa.Column("family_id", sa.String(length=64), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("user_agent", sa.String(length=400), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_sessions_user_id_users"),
        sa.UniqueConstraint("refresh_hash", name="uq_sessions_refresh_hash"),
        sa.PrimaryKeyConstraint("id", name="pk_sessions"),
    )
    op.create_index("ix_sessions_family_id", "sessions", ["family_id"])
    op.create_index("ix_sessions_user_family", "sessions", ["user_id", "family_id"])

    op.create_table(
        "targets",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("crop_code", sa.String(length=60), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("supported", sa.Boolean(), nullable=False),
        sa.Column("forecast_eligible", sa.Boolean(), nullable=False),
        sa.Column("taxonomy_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["crop_code"], ["crops.code"], name="fk_targets_crop_code_crops"),
        sa.UniqueConstraint("crop_code", "code", name="uq_target_crop_code"),
        sa.PrimaryKeyConstraint("id", name="pk_targets"),
    )
    op.create_index("ix_targets_crop_code", "targets", ["crop_code"])

    op.create_table(
        "user_area_assignments",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("geo_code", sa.String(length=64), nullable=False),
        sa.Column("level", sa.String(length=30), nullable=False),
        sa.Column("active_from", sa.DateTime(), nullable=False),
        sa.Column("active_to", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_user_area_assignments_user_id_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_area_assignments"),
    )
    op.create_index(
        "ix_area_assignments_user_active", "user_area_assignments", ["user_id", "active_to"]
    )
    op.create_index("ix_user_area_assignments_geo_code", "user_area_assignments", ["geo_code"])

    op.create_table(
        "user_permissions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("permission", sa.String(length=60), nullable=False),
        sa.Column("granted_by", sa.String(length=64), nullable=True),
        sa.Column("granted_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_user_permissions_user_id_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_permissions"),
    )
    op.create_index(
        "ix_user_permissions_user_active", "user_permissions", ["user_id", "revoked_at"]
    )
    op.create_index("ix_user_permissions_user_id", "user_permissions", ["user_id"])

    op.create_table(
        "user_roles",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("role_code", sa.String(length=40), nullable=False),
        sa.Column("granted_by", sa.String(length=64), nullable=True),
        sa.Column("granted_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["role_code"], ["roles.code"], name="fk_user_roles_role_code_roles"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_roles_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_user_roles"),
    )
    op.create_index("ix_user_roles_user_active", "user_roles", ["user_id", "revoked_at"])
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])

    op.create_table(
        "advisory_approvals",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("approver_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["approver_id"], ["users.id"], name="fk_advisory_approvals_approver_id_users"
        ),
        sa.ForeignKeyConstraint(
            ["version_id"],
            ["advisory_versions.id"],
            name="fk_advisory_approvals_version_id_advisory_versions",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_advisory_approvals"),
    )
    op.create_index("ix_advisory_approvals_version_id", "advisory_approvals", ["version_id"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("forecast_id", sa.String(length=64), nullable=False),
        sa.Column("geo_code", sa.String(length=64), nullable=False),
        sa.Column("target_code", sa.String(length=80), nullable=False),
        sa.Column("band", sa.String(length=30), nullable=False),
        sa.Column("window_from", sa.DateTime(), nullable=False),
        sa.Column("window_to", sa.DateTime(), nullable=False),
        sa.Column("message_version", sa.String(length=80), nullable=False),
        sa.Column("coverage", sa.String(length=20), nullable=False),
        sa.Column("reason_summary", sa.String(length=300), nullable=True),
        sa.Column("dedupe_key", sa.String(length=128), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["forecast_id"], ["forecasts.id"], name="fk_alerts_forecast_id_forecasts"
        ),
        sa.UniqueConstraint("dedupe_key", name="uq_alerts_dedupe_key"),
        sa.PrimaryKeyConstraint("id", name="pk_alerts"),
    )
    op.create_index("ix_alerts_forecast_id", "alerts", ["forecast_id"])

    op.create_table(
        "crop_cycles",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("growing_area_id", sa.String(length=64), nullable=False),
        sa.Column("crop_code", sa.String(length=60), nullable=False),
        sa.Column("variety", sa.String(length=120), nullable=True),
        sa.Column("planting_date", sa.DateTime(), nullable=True),
        sa.Column("stage", sa.String(length=40), nullable=True),
        sa.Column("stage_updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["crop_code"], ["crops.code"], name="fk_crop_cycles_crop_code_crops"
        ),
        sa.ForeignKeyConstraint(
            ["growing_area_id"],
            ["growing_areas.id"],
            name="fk_crop_cycles_growing_area_id_growing_areas",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_crop_cycles"),
    )
    op.create_index("ix_crop_cycles_growing_area_id", "crop_cycles", ["growing_area_id"])

    op.create_table(
        "observations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("client_report_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("subject_user_id", sa.String(length=64), nullable=True),
        sa.Column("growing_area_id", sa.String(length=64), nullable=True),
        sa.Column("area_code", sa.String(length=64), nullable=False),
        sa.Column("crop_code", sa.String(length=60), nullable=False),
        sa.Column("variety", sa.String(length=120), nullable=True),
        sa.Column("growth_stage", sa.String(length=40), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_observations_user_id_users"),
        sa.ForeignKeyConstraint(
            ["subject_user_id"], ["users.id"], name="fk_observations_subject_user_id_users"
        ),
        sa.ForeignKeyConstraint(
            ["crop_code"], ["crops.code"], name="fk_observations_crop_code_crops"
        ),
        sa.ForeignKeyConstraint(
            ["growing_area_id"],
            ["growing_areas.id"],
            name="fk_observations_growing_area_id_growing_areas",
        ),
        sa.UniqueConstraint("user_id", "client_report_id", name="uq_observation_client"),
        sa.PrimaryKeyConstraint("id", name="pk_observations"),
    )
    op.create_index(
        "ix_observations_area_status", "observations", ["area_code", "status", "created_at"]
    )
    op.create_index("ix_observations_user_created", "observations", ["user_id", "created_at"])

    op.create_table(
        "alert_deliveries",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("alert_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("provider_ref", sa.String(length=200), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("suppressed_reason", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_alert_deliveries_user_id_users"
        ),
        sa.ForeignKeyConstraint(
            ["alert_id"], ["alerts.id"], name="fk_alert_deliveries_alert_id_alerts"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_alert_deliveries"),
    )
    op.create_index("ix_alert_deliveries_alert_id", "alert_deliveries", ["alert_id"])
    op.create_index("ix_alert_deliveries_user_id", "alert_deliveries", ["user_id"])

    op.create_table(
        "image_assets",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("observation_id", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=400), nullable=False),
        sa.Column("original_width", sa.Integer(), nullable=True),
        sa.Column("original_height", sa.Integer(), nullable=True),
        sa.Column("bytes", sa.Integer(), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("mime", sa.String(length=80), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("compression", sa.JSON(), nullable=False),
        sa.Column("upload_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["observation_id"],
            ["observations.id"],
            name="fk_image_assets_observation_id_observations",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_image_assets"),
    )
    op.create_index("ix_image_assets_hash", "image_assets", ["content_hash"])
    op.create_index("ix_image_assets_observation_id", "image_assets", ["observation_id"])

    op.create_table(
        "review_assignments",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("observation_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("area_code", sa.String(length=64), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["observation_id"],
            ["observations.id"],
            name="fk_review_assignments_observation_id_observations",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_review_assignments_user_id_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_review_assignments"),
    )
    op.create_index(
        "ix_review_assignments_observation_id", "review_assignments", ["observation_id"]
    )

    op.create_table(
        "review_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("observation_id", sa.String(length=64), nullable=False),
        sa.Column("from_status", sa.String(length=30), nullable=True),
        sa.Column("to_status", sa.String(length=30), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["observation_id"],
            ["observations.id"],
            name="fk_review_events_observation_id_observations",
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], name="fk_review_events_actor_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_review_events"),
    )
    op.create_index(
        "ix_review_events_observation", "review_events", ["observation_id", "created_at"]
    )

    op.create_table(
        "review_requests",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("observation_id", sa.String(length=64), nullable=False),
        sa.Column("requested_by", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=300), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["requested_by"], ["users.id"], name="fk_review_requests_requested_by_users"
        ),
        sa.ForeignKeyConstraint(
            ["observation_id"],
            ["observations.id"],
            name="fk_review_requests_observation_id_observations",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_review_requests"),
    )
    op.create_index("ix_review_requests_observation_id", "review_requests", ["observation_id"])

    op.create_table(
        "reviews",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("observation_id", sa.String(length=64), nullable=False),
        sa.Column("reviewer_id", sa.String(length=64), nullable=False),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("reason_code", sa.String(length=60), nullable=True),
        sa.Column("corrected_label", sa.String(length=80), nullable=True),
        sa.Column("severity", sa.String(length=30), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("duplicate_of", sa.String(length=64), nullable=True),
        sa.Column("client_request_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], name="fk_reviews_reviewer_id_users"),
        sa.ForeignKeyConstraint(
            ["observation_id"], ["observations.id"], name="fk_reviews_observation_id_observations"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reviews"),
    )
    op.create_index("ix_reviews_observation_created", "reviews", ["observation_id", "created_at"])

    op.create_table(
        "alert_feedback",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("delivery_id", sa.String(length=64), nullable=False),
        sa.Column("rating", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["delivery_id"],
            ["alert_deliveries.id"],
            name="fk_alert_feedback_delivery_id_alert_deliveries",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_alert_feedback"),
    )
    op.create_index("ix_alert_feedback_delivery_id", "alert_feedback", ["delivery_id"])

    op.create_table(
        "image_predictions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("image_id", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=80), nullable=False),
        sa.Column("candidates", sa.JSON(), nullable=False),
        sa.Column("confidence_band", sa.String(length=20), nullable=True),
        sa.Column("calibrated", sa.Boolean(), nullable=False),
        sa.Column("abstained", sa.Boolean(), nullable=False),
        sa.Column("abstain_reason", sa.String(length=60), nullable=True),
        sa.Column("quality_flags", sa.JSON(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["image_id"], ["image_assets.id"], name="fk_image_predictions_image_id_image_assets"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_image_predictions"),
    )
    op.create_index("ix_image_predictions_image_id", "image_predictions", ["image_id"])

    op.create_table(
        "image_quality_results",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("image_id", sa.String(length=64), nullable=False),
        sa.Column("gate_version", sa.String(length=80), nullable=False),
        sa.Column("result", sa.String(length=20), nullable=False),
        sa.Column("flags", sa.JSON(), nullable=False),
        sa.Column("thresholds", sa.JSON(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["image_id"], ["image_assets.id"], name="fk_image_quality_results_image_id_image_assets"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_image_quality_results"),
    )
    op.create_index("ix_image_quality_results_image_id", "image_quality_results", ["image_id"])

    op.create_table(
        "message_attachments",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("message_id", sa.String(length=64), nullable=False),
        sa.Column("image_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["message_id"], ["messages.id"], name="fk_message_attachments_message_id_messages"
        ),
        sa.ForeignKeyConstraint(
            ["image_id"], ["image_assets.id"], name="fk_message_attachments_image_id_image_assets"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_message_attachments"),
    )
    op.create_index("ix_message_attachments_message_id", "message_attachments", ["message_id"])

    op.create_table(
        "observation_verification",
        sa.Column("observation_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("evidence_tier", sa.String(length=30), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("verified_by", sa.String(length=64), nullable=True),
        sa.Column("review_id", sa.String(length=64), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["verified_by"], ["users.id"], name="fk_observation_verification_verified_by_users"
        ),
        sa.ForeignKeyConstraint(
            ["observation_id"],
            ["observations.id"],
            name="fk_observation_verification_observation_id_observations",
        ),
        sa.ForeignKeyConstraint(
            ["review_id"], ["reviews.id"], name="fk_observation_verification_review_id_reviews"
        ),
        sa.PrimaryKeyConstraint("observation_id", name="pk_observation_verification"),
    )

    op.create_table(
        "review_evidence",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("review_id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["review_id"], ["reviews.id"], name="fk_review_evidence_review_id_reviews"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_review_evidence"),
    )
    op.create_index("ix_review_evidence_review_id", "review_evidence", ["review_id"])


def downgrade() -> None:
    # NOTE: indexes are dropped explicitly (0002/0003 style); unique
    # constraints die with their table. SQLite cannot ALTER constraints,
    # so no drop_constraint is emitted here.

    op.drop_index("ix_review_evidence_review_id", table_name="review_evidence")
    op.drop_table("review_evidence")
    op.drop_table("observation_verification")
    op.drop_index("ix_message_attachments_message_id", table_name="message_attachments")
    op.drop_table("message_attachments")
    op.drop_index("ix_image_quality_results_image_id", table_name="image_quality_results")
    op.drop_table("image_quality_results")
    op.drop_index("ix_image_predictions_image_id", table_name="image_predictions")
    op.drop_table("image_predictions")
    op.drop_index("ix_alert_feedback_delivery_id", table_name="alert_feedback")
    op.drop_table("alert_feedback")
    op.drop_index("ix_reviews_observation_created", table_name="reviews")
    op.drop_table("reviews")
    op.drop_index("ix_review_requests_observation_id", table_name="review_requests")
    op.drop_table("review_requests")
    op.drop_index("ix_review_events_observation", table_name="review_events")
    op.drop_table("review_events")
    op.drop_index("ix_review_assignments_observation_id", table_name="review_assignments")
    op.drop_table("review_assignments")
    op.drop_index("ix_image_assets_observation_id", table_name="image_assets")
    op.drop_index("ix_image_assets_hash", table_name="image_assets")
    op.drop_table("image_assets")
    op.drop_index("ix_alert_deliveries_user_id", table_name="alert_deliveries")
    op.drop_index("ix_alert_deliveries_alert_id", table_name="alert_deliveries")
    op.drop_table("alert_deliveries")
    op.drop_index("ix_observations_user_created", table_name="observations")
    op.drop_index("ix_observations_area_status", table_name="observations")
    op.drop_table("observations")
    op.drop_index("ix_crop_cycles_growing_area_id", table_name="crop_cycles")
    op.drop_table("crop_cycles")
    op.drop_index("ix_alerts_forecast_id", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_advisory_approvals_version_id", table_name="advisory_approvals")
    op.drop_table("advisory_approvals")
    op.drop_index("ix_user_roles_user_id", table_name="user_roles")
    op.drop_index("ix_user_roles_user_active", table_name="user_roles")
    op.drop_table("user_roles")
    op.drop_index("ix_user_permissions_user_id", table_name="user_permissions")
    op.drop_index("ix_user_permissions_user_active", table_name="user_permissions")
    op.drop_table("user_permissions")
    op.drop_index("ix_user_area_assignments_geo_code", table_name="user_area_assignments")
    op.drop_index("ix_area_assignments_user_active", table_name="user_area_assignments")
    op.drop_table("user_area_assignments")
    op.drop_index("ix_targets_crop_code", table_name="targets")
    op.drop_table("targets")
    op.drop_index("ix_sessions_user_family", table_name="sessions")
    op.drop_index("ix_sessions_family_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_notification_preferences_user_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")
    op.drop_table("idempotency_records")
    op.drop_index("ix_growing_areas_owner_user_id", table_name="growing_areas")
    op.drop_index("ix_growing_areas_geo_code", table_name="growing_areas")
    op.drop_table("growing_areas")
    op.drop_index("ix_forecasts_lookup", table_name="forecasts")
    op.drop_table("forecasts")
    op.drop_table("export_jobs")
    op.drop_index("ix_devices_user_id", table_name="devices")
    op.drop_table("devices")
    op.drop_index("ix_crop_calendars_lookup", table_name="crop_calendars")
    op.drop_table("crop_calendars")
    op.drop_index("ix_consents_user_type", table_name="consents")
    op.drop_table("consents")
    op.drop_index("ix_advisory_versions_advisory_id", table_name="advisory_versions")
    op.drop_table("advisory_versions")
    op.drop_index("ix_weather_geo_source", table_name="weather_snapshots")
    op.drop_table("weather_snapshots")
    op.drop_table("users")
    op.drop_table("system_configs")
    op.drop_table("roles")
    op.drop_index("ix_otp_phone_created", table_name="otp_codes")
    op.drop_table("otp_codes")
    op.drop_table("model_registry")
    op.drop_table("geographies")
    op.drop_table("forecast_runs")
    op.drop_table("feature_snapshots")
    op.drop_table("crops")
    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_index("ix_audit_entity", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_alert_policies_scope", table_name="alert_policies")
    op.drop_table("alert_policies")
    op.drop_index("ix_advisories_crop_code", table_name="advisories")
    op.drop_table("advisories")

    # NOTE: DROP EXTENSION fails if any non-ORM object (reference schema,
    # manual geometry) depends on PostGIS. On failure, keep the extension:
    # it is inert on a schema with no spatial columns.
    if _is_postgresql():
        try:
            op.execute("DROP EXTENSION IF EXISTS postgis")
        except Exception as exc:  # noqa: BLE001 - keep inert extension
            print(f"[0004] WARNING: postgis drop skipped ({exc})")

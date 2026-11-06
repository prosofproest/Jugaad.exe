"""Initial schema slice from 05-data-layer.md

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-11-06 15:40:00.000000

Implements the 14 schema slices:
  1. Identity (roles, users, user_roles, devices, consents, user_area_assignments, sessions)
  2. Geography & crop context (geographies, crops, targets, crop_calendars, growing_areas, crop_cycles)
  3. Observations & media (observations, image_assets, image_quality_results, image_predictions, review_requests)
  4. Reviews & verification (reviews, review_evidence, labels, review_events, observation_verification, review_assignments, sentinel_sites, sentinel_visits)
  5. Forecast & weather (weather_snapshots, feature_snapshots, forecasts, forecast_runs)
  6. Advisory & alerts (advisories, advisory_versions, advisory_approvals, alert_policies, alerts, alert_deliveries)
  7. Registry, audit & exports (model_registry, audit_events, export_jobs)
"""
from typing import Sequence, Union
import os
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Resolve 01-schema.sql path relative to this file or current working directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    schema_sql_path = os.path.join(base_dir, "schema", "01-schema.sql")

    if not os.path.exists(schema_sql_path):
        # Fallback to local schema path
        schema_sql_path = os.path.join("database", "schema", "01-schema.sql")

    with open(schema_sql_path, "r", encoding="utf-8") as f:
        ddl = f.read()

    # Execute DDL
    op.execute(sa.text(ddl))


def downgrade() -> None:
    # Drop views first
    op.execute(sa.text("DROP VIEW IF EXISTS v_demo_rows CASCADE;"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_sentinel_negative_candidates CASCADE;"))

    # Break circular FK on advisories -> advisory_versions
    op.execute(sa.text("ALTER TABLE IF EXISTS advisories DROP CONSTRAINT IF EXISTS fk_advisories_current_version CASCADE;"))

    # Drop tables in reverse dependency order
    tables = [
        "export_jobs",
        "audit_events",
        "model_registry",
        "alert_deliveries",
        "alerts",
        "alert_policies",
        "advisory_approvals",
        "advisory_versions",
        "advisories",
        "forecast_runs",
        "forecasts",
        "feature_snapshots",
        "weather_snapshots",
        "historical_occurrences",
        "sentinel_visits",
        "sentinel_sites",
        "review_assignments",
        "observation_verification",
        "review_events",
        "labels",
        "review_evidence",
        "reviews",
        "review_requests",
        "image_predictions",
        "image_quality_results",
        "image_assets",
        "observations",
        "crop_cycles",
        "growing_areas",
        "crop_calendars",
        "targets",
        "crops",
        "geographies",
        "sessions",
        "user_area_assignments",
        "consents",
        "devices",
        "user_roles",
        "users",
        "roles",
    ]

    for table in tables:
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table} CASCADE;"))

    # Drop custom functions
    functions = [
        "forecast_eligible_cases(timestamptz)",
        "suppress_small_count(integer, integer)",
        "labels_guard_mutation()",
        "reject_mutation()",
        "set_updated_at()",
    ]

    for func in functions:
        op.execute(sa.text(f"DROP FUNCTION IF EXISTS {func} CASCADE;"))


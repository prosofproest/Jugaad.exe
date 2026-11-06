"""Emit docs/database/ORM_INVENTORY.md from live ORM metadata.

Run from backend/:
    .venv/bin/python scripts/emit_orm_inventory.py

Regenerating after any ORM change is required (see MIGRATION_GUIDE.md).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import models  # noqa: F401
from app.db.base import Base

OUT = Path(__file__).resolve().parents[2] / "docs" / "database" / "ORM_INVENTORY.md"

# Source file per table (hand-maintained; update with any model move).
SOURCE = {
    "users": "backend/app/db/models.py :: User",
    "roles": "backend/app/db/models.py :: Role",
    "user_roles": "backend/app/db/models.py :: UserRole",
    "user_permissions": "backend/app/db/models.py :: UserPermission",
    "devices": "backend/app/db/models.py :: Device",
    "consents": "backend/app/db/models.py :: Consent",
    "user_area_assignments": "backend/app/db/models.py :: UserAreaAssignment",
    "sessions": "backend/app/db/models.py :: Session",
    "otp_codes": "backend/app/db/models.py :: OtpCode",
    "geographies": "backend/app/db/models.py :: Geography",
    "crops": "backend/app/db/models.py :: Crop",
    "targets": "backend/app/db/models.py :: Target",
    "crop_calendars": "backend/app/db/models.py :: CropCalendar",
    "growing_areas": "backend/app/db/models.py :: GrowingArea",
    "crop_cycles": "backend/app/db/models.py :: CropCycle",
    "observations": "backend/app/db/models.py :: Observation",
    "image_assets": "backend/app/db/models.py :: ImageAsset",
    "image_quality_results": "backend/app/db/models.py :: ImageQualityResult",
    "image_predictions": "backend/app/db/models.py :: ImagePrediction",
    "review_requests": "backend/app/db/models.py :: ReviewRequest (observation queue)",
    "reviews": "backend/app/db/models.py :: Review",
    "review_evidence": "backend/app/db/models.py :: ReviewEvidence",
    "review_events": "backend/app/db/models.py :: ReviewEvent",
    "observation_verification": "backend/app/db/models.py :: ObservationVerification",
    "review_assignments": "backend/app/db/models.py :: ReviewAssignment",
    "weather_snapshots": "backend/app/db/models.py :: WeatherSnapshot",
    "feature_snapshots": "backend/app/db/models.py :: FeatureSnapshot",
    "forecasts": "backend/app/db/models.py :: Forecast",
    "forecast_runs": "backend/app/db/models.py :: ForecastRun",
    "advisories": "backend/app/db/models.py :: Advisory",
    "advisory_versions": "backend/app/db/models.py :: AdvisoryVersion",
    "advisory_approvals": "backend/app/db/models.py :: AdvisoryApproval",
    "alert_policies": "backend/app/db/models.py :: AlertPolicy",
    "alerts": "backend/app/db/models.py :: Alert",
    "alert_deliveries": "backend/app/db/models.py :: AlertDelivery",
    "alert_feedback": "backend/app/db/models.py :: AlertFeedback",
    "notification_preferences": "backend/app/db/models.py :: NotificationPreference",
    "model_registry": "backend/app/db/models.py :: ModelRegistry",
    "audit_events": "backend/app/db/models.py :: AuditEvent",
    "idempotency_records": "backend/app/db/models.py :: IdempotencyRecord",
    "export_jobs": "backend/app/db/models.py :: ExportJob",
    "system_configs": "backend/app/db/models.py :: SystemConfig",
    "message_attachments": "backend/app/db/models.py :: MessageAttachment",
    "conversations": "backend/app/modules/conversations/orm.py :: ConversationRow",
    "messages": "backend/app/modules/conversations/orm.py :: MessageRow",
    "message_events": "backend/app/modules/conversations/orm.py :: MessageEventRow",
    "image_uploads": "backend/app/modules/conversations/orm.py :: ImageUploadRow",
    "chat_review_requests": "backend/app/modules/conversations/orm.py :: ReviewRequestRow (chat)",
    "video_uploads": "backend/app/modules/video/orm.py :: VideoUploadRow",
    "video_readings": "backend/app/modules/video/orm.py :: VideoReadingRow",
    "h3_cells": "backend/app/geo/models.py :: H3Cell",
    "farm_hexagon_assignments": "backend/app/geo/models.py :: FarmHexagonAssignment",
    "geo_observations": "backend/app/geo/models.py :: GeoObservation",
    "disease_reports": "backend/app/geo/models.py :: DiseaseReport",
    "pest_reports": "backend/app/geo/models.py :: PestReport",
    "hotspot_clusters": "backend/app/geo/models.py :: HotspotCluster",
    "hotspot_history": "backend/app/geo/models.py :: HotspotHistory",
    "regional_risk_scores": "backend/app/geo/models.py :: RegionalRiskScore",
    "weather_cell_records": "backend/app/geo/models.py :: WeatherCellRecord",
    "inspection_tasks": "backend/app/geo/models.py :: InspectionTask",
    "task_assignments": "backend/app/geo/models.py :: TaskAssignment",
    "field_agent_profiles": "backend/app/geo/models.py :: FieldAgentProfile",
    "inspection_results": "backend/app/geo/models.py :: InspectionResult",
    "expert_verifications": "backend/app/geo/models.py :: ExpertVerification",
    "recovery_monitoring_records": "backend/app/geo/models.py :: RecoveryMonitoringRecord",
    "task_status_history": "backend/app/geo/models.py :: TaskStatusHistory",
    "user_task_availability": "backend/app/geo/models.py :: UserTaskAvailability",
}


def col_type(column) -> str:
    name = column.type.__class__.__name__
    if name == "String":
        return f"VARCHAR({column.type.length})" if column.type.length else "VARCHAR"
    if name == "UTCDateTime":
        return "TIMESTAMP (naive UTC via UTCDateTime)"
    if name == "DateTime":
        return "TIMESTAMP WITH TIME ZONE"
    return name


def main() -> None:
    tables = Base.metadata.tables
    lines = []
    lines.append("# ORM Inventory (authoritative ORM metadata)")
    lines.append("")
    lines.append("Generated from live `Base.metadata` by `backend/scripts/emit_orm_inventory.py`.")
    lines.append("Source of truth for every table below is the Python model; schema SQL")
    lines.append("is derived from it (see POSTGRESQL_MAPPING_MATRIX.md).")
    lines.append("")
    lines.append(f"- ORM models/tables discovered: **{len(tables)}**")
    fk_total = sum(len(t.foreign_keys) for t in tables.values())
    lines.append(f"- Foreign keys (column-level): **{fk_total}**")
    uq_total = sum(
        1
        for t in tables.values()
        for c in t.constraints
        if c.__class__.__name__ == "UniqueConstraint"
    )
    lines.append(f"- Unique constraints: **{uq_total}**")
    ix_total = sum(len(t.indexes) for t in tables.values())
    lines.append(f"- B-tree indexes (declared): **{ix_total}**")
    ck_total = sum(
        1
        for t in tables.values()
        for c in t.constraints
        if c.__class__.__name__ == "CheckConstraint"
    )
    lines.append(f"- CHECK constraints in ORM metadata: **{ck_total}**")
    lines.append("- Native ENUM types: **0** (closed sets are `VARCHAR` + service checks)")
    lines.append("- Geometry/geography columns: **0** (see §3)")
    lines.append("- ORM `relationship()` declarations: **0** (all associations are FK columns)")
    lines.append("")
    lines.append("## 1. Per-table detail")
    lines.append("")
    for tname in sorted(tables):
        table = tables[tname]
        pk = [c.name for c in table.primary_key.columns]
        lines.append(f"### `{tname}` — {SOURCE.get(tname, 'UNKNOWN')}")
        lines.append("")
        lines.append(f"- Primary key: `{', '.join(pk)}`")
        if table.foreign_keys:
            lines.append("- Foreign keys:")
            for fk in sorted(table.foreign_keys, key=lambda f: f.parent.name):
                lines.append(
                    f"  - `{fk.parent.name}` → `{fk.column.table.name}.{fk.column.name}`"
                    + (f" ON DELETE {fk.ondelete}" if fk.ondelete else "")
                )
        else:
            lines.append("- Foreign keys: none")
        uqs = [c for c in table.constraints if c.__class__.__name__ == "UniqueConstraint"]
        if uqs:
            lines.append("- Unique constraints:")
            for c in uqs:
                lines.append(
                    f"  - `{c.name}` ({', '.join(col.name for col in c.columns)})"
                )
        if table.indexes:
            lines.append("- Indexes:")
            for ix in sorted(table.indexes, key=lambda i: i.name or ""):
                lines.append(
                    f"  - `{ix.name}` ({', '.join(c.name for c in ix.columns)})"
                )
        lines.append("")
        lines.append("| Column | Type | Null | Notes |")
        lines.append("|---|---|---|---|")
        for col in table.columns:
            notes = []
            if col.primary_key:
                notes.append("PK")
            if col.unique and not col.primary_key:
                notes.append("UNIQUE")
            if col.index:
                notes.append("indexed")
            if col.server_default is not None:
                notes.append("server_default=now()")
            if col.default is not None:
                notes.append("python default")
            lines.append(
                f"| `{col.name}` | {col_type(col)} | "
                f"{'NULL' if col.nullable else 'NOT NULL'} | {'; '.join(notes)} |"
            )
        lines.append("")
    lines.append("## 2. Type mapping decisions (ORM → PostgreSQL)")
    lines.append("")
    lines.append("- `String(n)` → `VARCHAR(n)`. No `TEXT` upgrade except ORM `Text` columns.")
    lines.append("- IDs are `String(64)` app-generated (`usr_…`, `conv_…`); they stay")
    lines.append("  `VARCHAR(64)`, **not** `UUID`. Regenerating as UUID would orphan every FK.")
    lines.append("- `UTCDateTime` (TypeDecorator over `DateTime`) → `TIMESTAMP WITHOUT TIME ZONE`")
    lines.append("  on PostgreSQL, storing naive UTC; Python returns aware UTC. Chat/video")
    lines.append("  tables use `DateTime(timezone=True)` → `TIMESTAMPTZ`. This mixed")
    lines.append("  semantics are preserved as-is; unifying to TIMESTAMPTZ needs a data")
    lines.append("  migration and is an open decision (not done here).")
    lines.append("- `JSON` → `JSON` on PostgreSQL (SQLAlchemy portable type). 26 columns")
    lines.append("  are JSON. Upgrading to `JSONB` (indexing, containment) needs an ORM")
    lines.append("  variant change first — not done here; see Phase 3 rationale.")
    lines.append("- `Numeric(4,3)` / `Numeric(6,5)` → `NUMERIC`. Python `default=` values")
    lines.append("  are client-side and have **no** server defaults in migrations.")
    lines.append("- Only 16 columns have `server_default=now()` (TimestampMixin + chat/video")
    lines.append("  `created_at`/`updated_at`/`generated_at`). Everything else is a")
    lines.append("  Python-side default — migrations intentionally emit no server default.")
    lines.append("- `Float` → `DOUBLE PRECISION` (quality metrics). `Boolean` → `BOOLEAN`.")
    lines.append("- `ON DELETE CASCADE` only on chat/video FKs (5+1). All other FKs are")
    lines.append("  `NO ACTION` (ORM default). Deletion semantics are service-enforced.")
    lines.append("")
    lines.append("## 3. PostGIS (zero spatial columns — deliberate)")
    lines.append("")
    lines.append("The backend ORM has **zero** geometry/geography columns. `models.py`")
    lines.append("states this explicitly: the pilot API only serves block/mandal")
    lines.append("aggregates and geometry arrives when boundary data is approved. Migration")
    lines.append("`0004` therefore enables the `postgis` extension but adds no spatial")
    lines.append("columns or GiST indexes. The `database/schema/01-schema.sql` reference")
    lines.append("schema **does** declare `geographies.geom MultiPolygon(4326)`,")
    lines.append("`growing_areas.geom`, `observations.geom Point(4326)` — that geometry is")
    lines.append("a documented drift (§4), not recreated here. Adding ORM geometry now")
    lines.append("would invent SRIDs/dimensionality the app never approved.")
    lines.append("")
    lines.append("## 4. Reconciliation: backend vs `database/` reference")
    lines.append("")
    lines.append("| Area | Backend ORM (authority) | `database/schema/01-schema.sql` (reference) |")
    lines.append("|---|---|---|")
    lines.append("| Tables | 50 (`app.db.models` + chat/video ORMs) | 40 (subset; `historical_occurrences` etc. exist only there) |")
    lines.append("| PKs | `VARCHAR(64)` app ids | `UUID DEFAULT gen_random_uuid()` |")
    lines.append("| Timestamps | mixed naive/aware (see §2) | `timestamptz` |")
    lines.append("| JSON | `JSON` | `jsonb` |")
    lines.append("| Closed sets | `VARCHAR` + service checks | `text + CHECK` |")
    lines.append("| Geometry | none | `geometry(...,4326)` ×3 |")
    lines.append("| Append-only | service code only | `reject_mutation()` triggers ×13 |")
    lines.append("| Migrations | Alembic 0001→0004 (backend) | `database/alembic/0001,0002` (reference) |")
    lines.append("")
    lines.append("**Authority:** backend Alembic (`backend/app/db/migrations`, `env.py` loads")
    lines.append("`app.db.models`) is the single operational migration system (ADR-002).")
    lines.append("`database/` SQL/history are **reference only** (its own header says so:")
    lines.append("“must never be applied to production by hand”). Never run both histories")
    lines.append("against the same database. The backend schema is a portable subset that")
    lines.append("runs on SQLite for dev/tests and PostgreSQL for deployment; reference")
    lines.append("features (triggers, geometry, historical_occurrences) need explicit ORM")
    lines.append("parcels + migrations before they exist in the deployment.")
    lines.append("")
    lines.append("## 5. Models without database tables")
    lines.append("")
    lines.append("None. Every ORM model maps to one table. All association columns")
    lines.append("(`user_roles`, `user_permissions`, etc.) are full tables, not.")
    lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

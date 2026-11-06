"""SQLite persistence for the runnable Phase-4 slice.

The production target is PostgreSQL 16 + PostGIS with SQLAlchemy/Alembic (see
``feature-specs/05-data-layer.md``). This module intentionally uses the Python
standard library's ``sqlite3`` so the forecast, advisory and alert paths can be
run and tested without infrastructure. The table shapes mirror the data-layer
spec, including append-only predictions and lineage columns, so a later
migration is additive rather than a rewrite.

Nothing in this module knows about HTTP. Repositories call these helpers.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .timeutil import to_iso, utcnow

_DEFAULT_PATH = Path(__file__).parent / "forecast.db"
_db_path: Path = Path(os.environ.get("JUGAAD_DB_PATH", _DEFAULT_PATH))


def configure(path: str | os.PathLike[str]) -> None:
    """Point the module at another database file (used by tests and seeds)."""

    global _db_path
    _db_path = Path(path)


def get_db_path() -> Path:
    return _db_path


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    """Yield a connection that is always closed, with foreign keys enabled."""

    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_registry (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    version TEXT NOT NULL UNIQUE,
    artefact_key TEXT,
    checksum TEXT,
    metrics_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL CHECK (status IN ('draft','validated','approved','retired')),
    is_demo INTEGER NOT NULL DEFAULT 0,
    approved_by TEXT,
    approved_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS geographies (
    code TEXT NOT NULL,
    level TEXT NOT NULL,
    name TEXT NOT NULL,
    parent_code TEXT,
    boundary_version TEXT NOT NULL,
    geom_geojson TEXT NOT NULL,
    valid_from TEXT,
    valid_to TEXT,
    PRIMARY KEY (code, boundary_version)
);

CREATE TABLE IF NOT EXISTS weather_snapshots (
    id TEXT PRIMARY KEY,
    geo_code TEXT NOT NULL,
    source TEXT NOT NULL,
    source_timestamp TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    variables_json TEXT NOT NULL,
    completeness REAL NOT NULL CHECK (completeness BETWEEN 0 AND 1),
    is_stale INTEGER NOT NULL DEFAULT 0,
    is_demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_weather_geo_time
    ON weather_snapshots(geo_code, source_timestamp DESC);

CREATE TABLE IF NOT EXISTS crop_stage_windows (
    id TEXT PRIMARY KEY,
    crop_code TEXT NOT NULL,
    geo_code TEXT NOT NULL,
    season TEXT NOT NULL,
    stage TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT NOT NULL,
    is_demo INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_stage_lookup
    ON crop_stage_windows(crop_code, geo_code, valid_from);

CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    reporter_id TEXT NOT NULL,
    geo_code TEXT NOT NULL,
    crop_code TEXT NOT NULL,
    target_code TEXT,
    verification_status TEXT NOT NULL CHECK (
        verification_status IN (
            'unverified','confirmed','probable','rejected',
            'duplicate','needs_visit','unresolved'
        )
    ),
    verified_at TEXT,
    event_date TEXT NOT NULL,
    reported_at TEXT NOT NULL,
    is_demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_obs_geo_event
    ON observations(geo_code, event_date);
CREATE INDEX IF NOT EXISTS idx_obs_verify
    ON observations(verification_status, verified_at);

CREATE TABLE IF NOT EXISTS feature_snapshots (
    id TEXT PRIMARY KEY,
    crop_code TEXT NOT NULL,
    target_code TEXT NOT NULL,
    geo_code TEXT NOT NULL,
    horizon_days INTEGER NOT NULL,
    issue_time TEXT NOT NULL,
    features_json TEXT NOT NULL,
    source_refs_json TEXT NOT NULL,
    coverage TEXT NOT NULL CHECK (coverage IN ('good','partial','low','unknown')),
    coverage_detail_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_snapshot_lookup
    ON feature_snapshots(crop_code, target_code, geo_code, issue_time DESC);

CREATE TABLE IF NOT EXISTS forecasts (
    id TEXT PRIMARY KEY,
    crop_code TEXT NOT NULL,
    target_code TEXT NOT NULL,
    geo_code TEXT NOT NULL,
    horizon_days INTEGER NOT NULL,
    issue_date TEXT NOT NULL,
    issue_time TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT NOT NULL,
    risk_band TEXT NOT NULL CHECK (
        risk_band IN ('low','moderate','high','urgent','insufficient_data')
    ),
    probability REAL CHECK (probability IS NULL OR (probability >= 0 AND probability <= 1)),
    confidence_band TEXT NOT NULL,
    coverage TEXT NOT NULL CHECK (coverage IN ('good','partial','low','unknown')),
    coverage_detail_json TEXT NOT NULL,
    drivers_json TEXT NOT NULL,
    reason_code TEXT,
    model_version TEXT NOT NULL,
    feature_snapshot_id TEXT NOT NULL REFERENCES feature_snapshots(id),
    boundary_version TEXT NOT NULL,
    is_demo INTEGER NOT NULL DEFAULT 0,
    forced INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_forecast_current
    ON forecasts(crop_code, target_code, geo_code, horizon_days, issue_date)
    WHERE forced = 0;
CREATE INDEX IF NOT EXISTS idx_forecast_lookup
    ON forecasts(crop_code, target_code, geo_code, issue_time DESC);

CREATE TABLE IF NOT EXISTS forecast_runs (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    model_version TEXT NOT NULL,
    areas_total INTEGER NOT NULL DEFAULT 0,
    areas_scored INTEGER NOT NULL DEFAULT 0,
    areas_insufficient INTEGER NOT NULL DEFAULT 0,
    error TEXT
);

CREATE TABLE IF NOT EXISTS advisories (
    id TEXT PRIMARY KEY,
    crop_code TEXT NOT NULL,
    target_code TEXT NOT NULL,
    geo_scope_json TEXT NOT NULL,
    language TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft','approved','withdrawn','expired')),
    current_version_id TEXT,
    is_demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_advisory_scope
    ON advisories(crop_code, target_code, language, status);

CREATE TABLE IF NOT EXISTS advisory_versions (
    id TEXT PRIMARY KEY,
    advisory_id TEXT NOT NULL REFERENCES advisories(id),
    version INTEGER NOT NULL,
    body_md TEXT NOT NULL,
    action_types_json TEXT NOT NULL,
    author_id TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (advisory_id, version)
);

CREATE TABLE IF NOT EXISTS advisory_approvals (
    id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL REFERENCES advisory_versions(id),
    approver_id TEXT NOT NULL,
    role TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS user_permissions (
    user_id TEXT NOT NULL,
    permission TEXT NOT NULL,
    granted_by TEXT,
    granted_at TEXT NOT NULL,
    revoked_at TEXT,
    PRIMARY KEY (user_id, permission)
);

CREATE TABLE IF NOT EXISTS alert_policies (
    id TEXT PRIMARY KEY,
    geo_code TEXT NOT NULL,
    target_code TEXT NOT NULL,
    min_band TEXT NOT NULL CHECK (min_band IN ('low','moderate','high','urgent')),
    min_coverage TEXT NOT NULL CHECK (min_coverage IN ('good','partial','low','unknown')),
    cooldown_hours INTEGER NOT NULL,
    channels_json TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    is_demo INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_policy_lookup
    ON alert_policies(geo_code, target_code, active);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    forecast_id TEXT NOT NULL REFERENCES forecasts(id),
    geo_code TEXT NOT NULL,
    target_code TEXT NOT NULL,
    band TEXT NOT NULL,
    window_from TEXT NOT NULL,
    window_to TEXT NOT NULL,
    message_version TEXT NOT NULL,
    message_json TEXT NOT NULL,
    dedupe_key TEXT NOT NULL UNIQUE,
    suppressed INTEGER NOT NULL DEFAULT 0,
    suppression_reason TEXT,
    is_demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_alert_lookup
    ON alerts(geo_code, target_code, created_at DESC);

CREATE TABLE IF NOT EXISTS alert_deliveries (
    id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL REFERENCES alerts(id),
    user_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('queued','sent','delivered','failed','suppressed','opted_out')
    ),
    provider_ref TEXT,
    error TEXT,
    sent_at TEXT,
    delivered_at TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_delivery_alert
    ON alert_deliveries(alert_id, user_id);

CREATE TABLE IF NOT EXISTS alert_feedback (
    id TEXT PRIMARY KEY,
    delivery_id TEXT NOT NULL REFERENCES alert_deliveries(id),
    rating TEXT NOT NULL CHECK (rating IN ('useful','not_useful','inaccurate')),
    reason TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notification_preferences (
    user_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    target_code TEXT NOT NULL DEFAULT '*',
    opted_in INTEGER NOT NULL DEFAULT 1,
    language TEXT NOT NULL DEFAULT 'en',
    quiet_hours_json TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, channel, target_code)
);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    actor_id TEXT,
    actor_role TEXT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    reason TEXT,
    request_id TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_entity
    ON audit_events(entity_type, entity_id, created_at DESC);
"""


def init_db() -> None:
    """Create every table and index. Idempotent."""

    with connection() as conn:
        conn.executescript(SCHEMA)
        conn.execute(
            "INSERT OR REPLACE INTO schema_meta(key, value) VALUES (?, ?)",
            ("phase4_schema_version", "2026-11-06.1"),
        )


def execute(sql: str, params: tuple[Any, ...] = ()) -> None:
    with connection() as conn:
        conn.execute(sql, params)


def query(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def query_one(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def insert(table: str, values: dict[str, Any]) -> None:
    """Insert one row. Column names are developer-controlled, never user input."""

    columns = list(values)
    placeholders = ", ".join("?" for _ in columns)
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    execute(sql, tuple(values[column] for column in columns))


def json_text(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, default=str)


def json_load(value: str | None, default: Any = None) -> Any:
    if value is None or value == "":
        return default
    return json.loads(value)


def audit(
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    *,
    actor_id: str | None = None,
    actor_role: str | None = None,
    reason: str | None = None,
    request_id: str | None = None,
) -> None:
    """Append an audit event. Payloads never include free text or PII."""

    from .ids import new_id

    insert(
        "audit_events",
        {
            "id": new_id("aud"),
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "reason": reason,
            "request_id": request_id,
            "created_at": to_iso(utcnow()),
        },
    )

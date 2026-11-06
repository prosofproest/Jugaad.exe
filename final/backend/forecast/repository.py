"""Persistence queries for weather, crop stage, snapshots and forecasts.

Repositories do not make decisions; they read and write rows. The service
layer owns gating, scoring, idempotency and serialisation.
"""

from __future__ import annotations

from typing import Any, Sequence

from .. import db
from ..ids import new_id
from ..timeutil import to_iso, utcnow


# --------------------------------------------------------------------- weather
def insert_weather_snapshot(
    *,
    geo_code: str,
    source: str,
    source_timestamp: str,
    variables: dict[str, Any],
    completeness: float = 1.0,
    fetched_at: str | None = None,
    is_stale: bool = False,
    is_demo: bool = True,
) -> str:
    snapshot_id = new_id("wx")
    db.insert(
        "weather_snapshots",
        {
            "id": snapshot_id,
            "geo_code": geo_code,
            "source": source,
            "source_timestamp": source_timestamp,
            "fetched_at": fetched_at or to_iso(utcnow()),
            "variables_json": db.json_text(variables),
            "completeness": completeness,
            "is_stale": int(is_stale),
            "is_demo": int(is_demo),
            "created_at": to_iso(utcnow()),
        },
    )
    return snapshot_id


def list_weather_snapshots(
    geo_code: str, since: str, until: str | None = None
) -> list[dict[str, Any]]:
    if until:
        rows = db.query(
            """
            SELECT * FROM weather_snapshots
            WHERE geo_code = ? AND source_timestamp >= ? AND source_timestamp <= ?
            ORDER BY source_timestamp ASC
            """,
            (geo_code, since, until),
        )
    else:
        rows = db.query(
            """
            SELECT * FROM weather_snapshots
            WHERE geo_code = ? AND source_timestamp >= ?
            ORDER BY source_timestamp ASC
            """,
            (geo_code, since),
        )
    return rows


# ----------------------------------------------------------------- crop stage
def insert_crop_stage(
    *,
    crop_code: str,
    geo_code: str,
    season: str,
    stage: str,
    valid_from: str,
    valid_to: str,
    is_demo: bool = True,
) -> str:
    stage_id = new_id("stage")
    db.insert(
        "crop_stage_windows",
        {
            "id": stage_id,
            "crop_code": crop_code,
            "geo_code": geo_code,
            "season": season,
            "stage": stage,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "is_demo": int(is_demo),
        },
    )
    return stage_id


def get_crop_stage(
    crop_code: str, geo_code: str, at: str
) -> dict[str, Any] | None:
    return db.query_one(
        """
        SELECT * FROM crop_stage_windows
        WHERE crop_code = ? AND geo_code = ?
          AND valid_from <= ? AND valid_to >= ?
        ORDER BY valid_from DESC LIMIT 1
        """,
        (crop_code, geo_code, at, at),
    )


# ----------------------------------------------------------------- observations
def insert_observation(
    *,
    reporter_id: str,
    geo_code: str,
    crop_code: str,
    target_code: str | None,
    verification_status: str,
    event_date: str,
    reported_at: str,
    verified_at: str | None = None,
    is_demo: bool = True,
) -> str:
    observation_id = new_id("obs")
    db.insert(
        "observations",
        {
            "id": observation_id,
            "reporter_id": reporter_id,
            "geo_code": geo_code,
            "crop_code": crop_code,
            "target_code": target_code,
            "verification_status": verification_status,
            "verified_at": verified_at,
            "event_date": event_date,
            "reported_at": reported_at,
            "is_demo": int(is_demo),
            "created_at": to_iso(utcnow()),
        },
    )
    return observation_id


def list_observations(
    geo_codes: Sequence[str], since: str, until: str | None = None
) -> list[dict[str, Any]]:
    geos = list(geo_codes)
    if not geos:
        return []
    placeholders = ", ".join("?" for _ in geos)
    params: list[Any] = list(geos) + [since]
    sql = f"""
        SELECT * FROM observations
        WHERE geo_code IN ({placeholders}) AND reported_at >= ?
    """
    if until:
        sql += " AND reported_at <= ?"
        params.append(until)
    sql += " ORDER BY reported_at ASC"
    return db.query(sql, tuple(params))


# ----------------------------------------------------------------- registry
def register_model(
    *,
    kind: str,
    version: str,
    status: str,
    artefact_key: str | None = None,
    checksum: str | None = None,
    metrics: dict[str, Any] | None = None,
    is_demo: bool = False,
    approved_by: str | None = None,
    approved_at: str | None = None,
) -> str:
    registry_id = new_id("mdl")
    db.insert(
        "model_registry",
        {
            "id": registry_id,
            "kind": kind,
            "version": version,
            "artefact_key": artefact_key,
            "checksum": checksum,
            "metrics_json": db.json_text(metrics or {}),
            "status": status,
            "is_demo": int(is_demo),
            "approved_by": approved_by,
            "approved_at": approved_at,
            "created_at": to_iso(utcnow()),
        },
    )
    return registry_id


def get_model_registry(version: str) -> dict[str, Any] | None:
    return db.query_one(
        "SELECT * FROM model_registry WHERE version = ?", (version,)
    )


# ------------------------------------------------------------------ snapshots
def insert_feature_snapshot(
    *,
    crop_code: str,
    target_code: str,
    geo_code: str,
    horizon_days: int,
    issue_time: str,
    features: dict[str, Any],
    source_refs: dict[str, Any],
    coverage: str,
    coverage_detail: dict[str, Any],
) -> str:
    snapshot_id = new_id("fs")
    db.insert(
        "feature_snapshots",
        {
            "id": snapshot_id,
            "crop_code": crop_code,
            "target_code": target_code,
            "geo_code": geo_code,
            "horizon_days": horizon_days,
            "issue_time": issue_time,
            "features_json": db.json_text(features),
            "source_refs_json": db.json_text(source_refs),
            "coverage": coverage,
            "coverage_detail_json": db.json_text(coverage_detail),
            "created_at": to_iso(utcnow()),
        },
    )
    return snapshot_id


def get_feature_snapshot(snapshot_id: str) -> dict[str, Any] | None:
    return db.query_one(
        "SELECT * FROM feature_snapshots WHERE id = ?", (snapshot_id,)
    )


# ------------------------------------------------------------------- forecasts
def find_current_forecast(
    *,
    crop_code: str,
    target_code: str,
    geo_code: str,
    horizon_days: int,
    issue_date: str,
) -> dict[str, Any] | None:
    return db.query_one(
        """
        SELECT * FROM forecasts
        WHERE crop_code = ? AND target_code = ? AND geo_code = ?
          AND horizon_days = ? AND issue_date = ? AND forced = 0
        ORDER BY created_at DESC LIMIT 1
        """,
        (crop_code, target_code, geo_code, horizon_days, issue_date),
    )


def insert_forecast(record: dict[str, Any]) -> str:
    forecast_id = record.get("id") or new_id("fcst")
    values = dict(record)
    values["id"] = forecast_id
    db.insert("forecasts", values)
    return forecast_id


def get_forecast(forecast_id: str) -> dict[str, Any] | None:
    return db.query_one("SELECT * FROM forecasts WHERE id = ?", (forecast_id,))


def query_forecasts(
    *,
    crop_code: str | None = None,
    target_code: str | None = None,
    geo_code: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    for column, value in (
        ("crop_code", crop_code),
        ("target_code", target_code),
        ("geo_code", geo_code),
    ):
        if value:
            clauses.append(f"{column} = ?")
            params.append(value)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(max(1, min(limit, 200)))
    return db.query(
        f"SELECT * FROM forecasts {where} ORDER BY issue_time DESC LIMIT ?",
        tuple(params),
    )


def latest_forecasts_for_layer(
    *,
    geo_code: str | None = None,
    target_code: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """Latest non-superseded forecast per crop/target/geo."""

    clauses = ["1 = 1"]
    params: list[Any] = []
    if geo_code:
        clauses.append("geo_code = ?")
        params.append(geo_code)
    if target_code:
        clauses.append("target_code = ?")
        params.append(target_code)
    params.append(max(1, min(limit, 2000)))
    sql = f"""
        SELECT f.*
        FROM forecasts f
        JOIN (
            SELECT crop_code, target_code, geo_code, MAX(issue_time) AS issue_time
            FROM forecasts
            WHERE {' AND '.join(clauses)}
            GROUP BY crop_code, target_code, geo_code
        ) newest
          ON newest.crop_code = f.crop_code
         AND newest.target_code = f.target_code
         AND newest.geo_code = f.geo_code
         AND newest.issue_time = f.issue_time
        ORDER BY f.geo_code, f.target_code
        LIMIT ?
    """
    return db.query(sql, tuple(params))


# ---------------------------------------------------------------- forecast run
def start_run(model_version: str, areas_total: int) -> str:
    run_id = new_id("run")
    db.insert(
        "forecast_runs",
        {
            "id": run_id,
            "started_at": to_iso(utcnow()),
            "finished_at": None,
            "status": "running",
            "model_version": model_version,
            "areas_total": areas_total,
            "areas_scored": 0,
            "areas_insufficient": 0,
            "error": None,
        },
    )
    return run_id


def finish_run(
    run_id: str,
    *,
    status: str,
    areas_scored: int,
    areas_insufficient: int,
    error: str | None = None,
) -> None:
    db.execute(
        """
        UPDATE forecast_runs
        SET finished_at = ?, status = ?, areas_scored = ?,
            areas_insufficient = ?, error = ?
        WHERE id = ?
        """,
        (
            to_iso(utcnow()),
            status,
            areas_scored,
            areas_insufficient,
            error,
            run_id,
        ),
    )

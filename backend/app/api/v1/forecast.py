"""Area outlook, map layers, coverage and admin forecast operations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.core.errors import ApiError
from app.db.models import (
    Crop,
    ForecastRun,
    Geography,
    ModelRegistry,
    SystemConfig,
    Target,
    User,
)
from app.db.session import get_db
from app.modules.audit.service import record_audit
from app.modules.forecast import service

router = APIRouter(tags=["forecast"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])

CONFIG_KEYS = {
    "risk_band_thresholds",
    "coverage_min_active_reporters",
    "small_count_threshold",
    "forecast_horizon_days",
    "boundary_version",
    "consent_version",
}


class GenerateForecastRequest(BaseModel):
    crop_code: str
    target_code: str
    geo_code: str
    force: bool = False


class ConfigUpdate(BaseModel):
    value: dict
    reason: str = Field(min_length=10, max_length=1000)


class ModelApproval(BaseModel):
    status: str
    notes: str | None = None


@router.get("/forecasts")
def list_forecasts(
    crop: str | None = None,
    target: str | None = None,
    geo: str | None = None,
    horizon_days: int | None = Query(default=None, ge=1, le=30),
    include_demo: bool = True,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return service.list_forecasts(
        db,
        crop=crop,
        target=target,
        geo=geo,
        horizon_days=horizon_days,
        include_demo=include_demo,
    )


@router.get("/forecasts/{forecast_id}")
def get_forecast(
    forecast_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return service.get_forecast(db, forecast_id)


@router.get("/coverage")
def get_coverage(
    geo: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if db.scalar(select(Geography).where(Geography.code == geo)) is None:
        raise ApiError(404, "not_found", "Area code is not recognised")
    return {"geo_code": geo, **service.coverage_for_area(db, geo)}


@router.get("/map/layers/{layer}")
def get_map_layer(
    layer: str,
    crop: str | None = None,
    target: str | None = None,
    date: str | None = None,
    bbox: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return service.map_layer(
        db, layer=layer, bbox=bbox, crop=crop, target=target, date_filter=date
    )


@admin_router.post("/forecasts/generate")
def generate_forecast(
    payload: GenerateForecastRequest,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict:
    forecast, created = service.generate_forecast(
        db,
        actor=user,
        crop_code=payload.crop_code,
        target_code=payload.target_code,
        geo_code=payload.geo_code,
        force=payload.force,
    )
    db.commit()
    return {
        "created": created,
        "forecast": service.serialize_forecast(forecast),
    }


@admin_router.post("/forecasts/generate-batch")
def generate_batch(
    force: bool = False,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict:
    results = []
    blocks = db.scalars(select(Geography).where(Geography.level == "block")).all()
    crops = db.scalars(select(Crop).where(Crop.supported.is_(True))).all()
    for crop in crops:
        targets = db.scalars(
            select(Target).where(
                Target.crop_code == crop.code,
                Target.supported.is_(True),
                Target.forecast_eligible.is_(True),
            )
        ).all()
        for target in targets:
            for block in blocks:
                try:
                    forecast, created = service.generate_forecast(
                        db,
                        actor=user,
                        crop_code=crop.code,
                        target_code=target.code,
                        geo_code=block.code,
                        force=force,
                    )
                    results.append(
                        {
                            "geo_code": block.code,
                            "crop_code": crop.code,
                            "target_code": target.code,
                            "forecast_id": forecast.id,
                            "created": created,
                            "risk_band": forecast.risk_band,
                            "reason_code": forecast.reason_code,
                            "is_demo": forecast.is_demo,
                        }
                    )
                except ApiError as error:
                    results.append(
                        {
                            "geo_code": block.code,
                            "crop_code": crop.code,
                            "target_code": target.code,
                            "error": error.code,
                        }
                    )
    db.commit()
    return {"items": results}


@admin_router.get("/forecast-runs")
def list_forecast_runs(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict:
    rows = db.scalars(
        select(ForecastRun).order_by(ForecastRun.started_at.desc()).limit(limit)
    ).all()
    return {
        "items": [
            {
                "run_id": row.id,
                "started_at": row.started_at.isoformat(),
                "finished_at": row.finished_at.isoformat() if row.finished_at else None,
                "status": row.status,
                "model_version": row.model_version,
                "areas_total": row.areas_total,
                "areas_scored": row.areas_scored,
                "areas_insufficient": row.areas_insufficient,
                "error": row.error,
            }
            for row in rows
        ]
    }


@admin_router.get("/config")
def list_config(
    user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)
) -> dict:
    rows = db.scalars(select(SystemConfig).order_by(SystemConfig.key)).all()
    return {
        "items": [
            {
                "key": row.key,
                "value": row.value,
                "updated_by": row.updated_by,
                "updated_at": row.updated_at.isoformat(),
            }
            for row in rows
        ]
    }


@admin_router.put("/config/{key}")
def update_config(
    key: str,
    payload: ConfigUpdate,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict:
    if key not in CONFIG_KEYS:
        raise ApiError(422, "unknown_config_key", "Configuration key is not managed here")
    if key == "risk_band_thresholds":
        required = {"low", "moderate", "high", "urgent"}
        missing = required - set(payload.value)
        if missing:
            raise ApiError(
                422,
                "invalid_thresholds",
                "All risk band thresholds are required",
                detail=f"Missing: {', '.join(sorted(missing))}",
            )
    row = db.get(SystemConfig, key)
    if row is None:
        row = SystemConfig(key=key, value={"value": payload.value}, updated_by=user.id)
        db.add(row)
    else:
        row.value = {"value": payload.value}
        row.updated_by = user.id
    record_audit(
        db,
        action="config.updated",
        actor=user,
        entity_type="system_config",
        entity_id=key,
        reason=payload.reason,
        detail={"value": payload.value},
    )
    db.commit()
    return {"key": key, "value": row.value, "updated_by": row.updated_by}


@admin_router.get("/models")
def list_models(
    user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)
) -> dict:
    rows = db.scalars(select(ModelRegistry).order_by(ModelRegistry.created_at.desc())).all()
    return {
        "items": [
            {
                "model_id": row.id,
                "kind": row.kind,
                "version": row.version,
                "status": row.status,
                "metrics": row.metrics,
                "approved_by": row.approved_by,
                "approved_at": row.approved_at.isoformat()
                if row.approved_at
                else None,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }


@admin_router.post("/models/{model_id}/status")
def set_model_status(
    model_id: str,
    payload: ModelApproval,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict:
    from datetime import datetime, timezone

    if payload.status not in {"approved", "rejected", "retired"}:
        raise ApiError(422, "invalid_model_status", "Unknown model status")
    row = db.get(ModelRegistry, model_id)
    if row is None:
        raise ApiError(404, "not_found", "Model version not found")
    if payload.status == "approved" and not payload.notes:
        raise ApiError(
            422,
            "approval_note_required",
            "An approval note is required for a model version",
        )
    row.status = payload.status
    row.approved_by = user.id
    row.approved_at = datetime.now(timezone.utc)
    record_audit(
        db,
        action="model.status_changed",
        actor=user,
        entity_type="model_registry",
        entity_id=row.id,
        reason=payload.notes,
        detail={"status": payload.status, "version": row.version},
    )
    db.commit()
    return {
        "model_id": row.id,
        "version": row.version,
        "status": row.status,
        "approved_by": row.approved_by,
    }

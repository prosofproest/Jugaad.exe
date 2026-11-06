"""Area outlook generation, coverage, no-score gate and map layers.

Photo assessment never appears in these responses. Each layer is returned
separately and the API never builds a merged "risk" layer.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.models import (
    Advisory,
    AdvisoryApproval,
    AdvisoryVersion,
    Crop,
    CropCalendar,
    FeatureSnapshot,
    Forecast,
    ForecastRun,
    Geography,
    ModelRegistry,
    Observation,
    ObservationVerification,
    Target,
    User,
    WeatherSnapshot,
)
from app.modules.audit.service import record_audit
from app.modules.forecast.rules import score_weather
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def _now() -> datetime:
    return datetime.now(UTC)


def _as_float(value) -> float | None:
    return None if value is None else float(value)


def is_stale(forecast: Forecast, now: datetime | None = None) -> bool:
    return forecast.valid_to < (now or _now())


def serialize_forecast(forecast: Forecast) -> dict:
    return {
        "forecast_id": forecast.id,
        "crop": forecast.crop_code,
        "target": forecast.target_code,
        "geography": {"level": "block", "code": forecast.geo_code},
        "horizon": "nowcast_10d" if forecast.horizon_days == 10 else f"{forecast.horizon_days}d",
        "horizon_days": forecast.horizon_days,
        "issue_time": forecast.issue_time.isoformat(),
        "valid_from": forecast.valid_from.isoformat(),
        "valid_to": forecast.valid_to.isoformat(),
        "risk_band": forecast.risk_band,
        "probability": _as_float(forecast.probability),
        "confidence": forecast.confidence_band,
        "coverage": forecast.coverage,
        "coverage_detail": forecast.coverage_detail,
        "drivers": list(forecast.drivers),
        "reason_code": forecast.reason_code,
        "model_version": forecast.model_version,
        "feature_snapshot_id": forecast.feature_snapshot_id,
        "boundary_version": forecast.boundary_version,
        "is_stale": is_stale(forecast),
        "is_demo": forecast.is_demo,
        "notice": "Area-wide early outlook, not a confirmed outbreak.",
    }


def list_forecasts(
    db: Session,
    *,
    crop: str | None,
    target: str | None,
    geo: str | None,
    horizon_days: int | None,
    include_demo: bool = True,
) -> dict:
    query = select(Forecast)
    if crop:
        query = query.where(Forecast.crop_code == crop)
    if target:
        query = query.where(Forecast.target_code == target)
    if geo:
        query = query.where(Forecast.geo_code == geo)
    if horizon_days:
        query = query.where(Forecast.horizon_days == horizon_days)
    if not include_demo:
        query = query.where(Forecast.is_demo.is_(False))
    rows = db.scalars(query.order_by(Forecast.issue_time.desc())).all()
    latest: dict[tuple, Forecast] = {}
    for row in rows:
        key = (row.crop_code, row.target_code, row.geo_code, row.horizon_days)
        latest.setdefault(key, row)
    items = [serialize_forecast(row) for row in latest.values()]
    return {"items": items, "next_cursor": None}


def get_forecast(db: Session, forecast_id: str) -> dict:
    forecast = db.get(Forecast, forecast_id)
    if forecast is None:
        raise ApiError(404, "not_found", "Forecast not found")
    payload = serialize_forecast(forecast)
    snapshot = (
        db.get(FeatureSnapshot, forecast.feature_snapshot_id)
        if forecast.feature_snapshot_id
        else None
    )
    advisories = db.scalars(
        select(Advisory).where(
            Advisory.crop_code == forecast.crop_code,
            Advisory.target_code == forecast.target_code,
            Advisory.status == "published",
        )
    ).all()
    valid_advisories = []
    for advisory in advisories:
        version = (
            db.get(AdvisoryVersion, advisory.current_version_id)
            if advisory.current_version_id
            else None
        )
        if (
            version is not None
            and version.valid_from <= _now() <= version.valid_to
            and db.scalar(select(AdvisoryApproval).where(AdvisoryApproval.version_id == version.id))
            is not None
            and (not advisory.geo_scope or forecast.geo_code in advisory.geo_scope)
        ):
            valid_advisories.append(
                {"advisory_id": advisory.id, "version": version.version, "title": advisory.title}
            )
    payload["lineage"] = {
        "feature_snapshot_id": forecast.feature_snapshot_id,
        "features": snapshot.features if snapshot else None,
        "source_refs": snapshot.source_refs if snapshot else None,
        "model_version": forecast.model_version,
        "generated_at": forecast.created_at.isoformat(),
    }
    payload["advisory_links"] = valid_advisories
    payload["band_rationale"] = {
        "drivers": list(forecast.drivers),
        "coverage": forecast.coverage,
        "calibrated": forecast.probability is not None,
    }
    return payload


def _latest_weather(db: Session, geo_code: str) -> WeatherSnapshot | None:
    return db.scalar(
        select(WeatherSnapshot)
        .where(WeatherSnapshot.geo_code == geo_code)
        .order_by(WeatherSnapshot.source_timestamp.desc())
    )


def coverage_for_area(db: Session, geo_code: str, *, now: datetime | None = None) -> dict:
    now = now or _now()
    cutoff = now - timedelta(days=14)
    verified = (
        db.scalar(
            select(func.count(Observation.id))
            .join(
                ObservationVerification,
                ObservationVerification.observation_id == Observation.id,
            )
            .where(
                Observation.area_code == geo_code,
                ObservationVerification.status.in_(["confirmed", "probable"]),
            )
        )
        or 0
    )
    active_reporters = (
        db.scalar(
            select(func.count(func.distinct(Observation.user_id))).where(
                Observation.area_code == geo_code,
                Observation.created_at >= cutoff,
                Observation.deleted_at.is_(None),
            )
        )
        or 0
    )
    weather = _latest_weather(db, geo_code)
    completeness = float(weather.completeness) if weather else 0.0
    verified = int(verified)
    active_reporters = int(active_reporters)
    details = {
        "verified_reports_14d": verified,
        "active_reporters": active_reporters,
        "weather_completeness": round(completeness, 3),
        "weather_fetched_at": weather.fetched_at.isoformat() if weather else None,
        "weather_is_demo": weather.is_demo if weather else None,
    }
    if active_reporters == 0 and completeness == 0:
        coverage = "unknown"
    elif active_reporters >= 3 and completeness >= 0.9:
        coverage = "good"
    elif active_reporters >= 1 and completeness >= 0.6:
        coverage = "partial"
    else:
        coverage = "low"
    return {"coverage": coverage, "detail": details}


def _config_value(db: Session, key: str, default):
    from app.db.models import SystemConfig

    row = db.get(SystemConfig, key)
    if row is None or not isinstance(row.value, dict):
        return default
    return row.value.get("value", default)


def generate_forecast(
    db: Session,
    *,
    actor: User | None,
    crop_code: str,
    target_code: str,
    geo_code: str,
    force: bool = False,
) -> tuple[Forecast, bool]:
    settings = get_settings()
    crop = db.get(Crop, crop_code)
    target = db.scalar(
        select(Target).where(Target.crop_code == crop_code, Target.code == target_code)
    )
    if crop is None or not crop.supported:
        raise ApiError(422, "unsupported_crop", "Crop is not on the validated allowlist")
    if target is None or not target.supported or not target.forecast_eligible:
        raise ApiError(422, "unsupported_target", "Target is not forecast-eligible")
    geo = db.scalar(select(Geography).where(Geography.code == geo_code))
    if geo is None:
        raise ApiError(422, "unknown_area", "Area code is not recognised")

    model = db.scalar(
        select(ModelRegistry).where(
            ModelRegistry.kind == "forecast",
            ModelRegistry.version == settings.forecast_model_version,
        )
    )
    if model is None or model.status != "approved":
        raise ApiError(
            409,
            "model_not_approved",
            "The forecast model is not approved; no forecast is generated",
        )

    now = _now()
    horizon = settings.forecast_horizon_days
    # Idempotency: one current forecast per crop/target/geo/horizon/issue date.
    same_day = db.scalar(
        select(Forecast)
        .where(
            Forecast.crop_code == crop_code,
            Forecast.target_code == target_code,
            Forecast.geo_code == geo_code,
            Forecast.horizon_days == horizon,
            Forecast.issue_time >= now.replace(hour=0, minute=0, second=0, microsecond=0),
        )
        .order_by(Forecast.issue_time.desc())
    )
    if same_day is not None and not force:
        return same_day, False

    run = ForecastRun(
        started_at=now,
        status="running",
        model_version=settings.forecast_model_version,
        areas_total=1,
    )
    db.add(run)

    weather = _latest_weather(db, geo_code)
    coverage = coverage_for_area(db, geo_code, now=now)
    calendar = db.scalar(
        select(CropCalendar).where(
            CropCalendar.crop_code == crop_code, CropCalendar.geo_code == geo_code
        )
    )
    configured_boundary = _config_value(db, "boundary_version", geo.boundary_version)

    reason_code: str | None = None
    if weather is None or weather.source_timestamp < now - timedelta(
        hours=settings.weather_stale_hours
    ):
        reason_code = "weather_stale"
    elif coverage["coverage"] in {"low", "unknown"}:
        reason_code = "insufficient_coverage"
    elif calendar is None:
        reason_code = "calendar_missing"
    elif geo.boundary_version != configured_boundary:
        reason_code = "boundary_mismatch"

    features: dict = {
        "gate": {
            "weather_stale": reason_code == "weather_stale",
            "coverage": coverage["coverage"],
            "calendar_present": calendar is not None,
            "boundary_version": geo.boundary_version,
            "configured_boundary_version": configured_boundary,
        },
        "coverage": coverage["detail"],
    }
    drivers: list[str] = []
    risk_band = "insufficient_data"
    probability = None
    confidence = "not_calibrated"

    if reason_code is None:
        variables = dict(weather.variables or {})
        features.update(
            {
                "weather": variables,
                "weather_source_timestamp": weather.source_timestamp.isoformat(),
                "crop_stage": "vegetative",
                "verified_reports_14d": coverage["detail"]["verified_reports_14d"],
            }
        )
        thresholds = _config_value(db, "risk_band_thresholds", {})
        result = score_weather(
            variables,
            verified_reports_14d=coverage["detail"]["verified_reports_14d"],
            thresholds=thresholds,
        )
        drivers = list(result.drivers)
        risk_band = result.risk_band
        features["rule_score"] = result.score
        features["rule_result"] = result.as_feature_dict()

    snapshot = FeatureSnapshot(
        crop_code=crop_code,
        target_code=target_code,
        geo_code=geo_code,
        horizon_days=horizon,
        issue_time=now,
        features=features,
        source_refs={
            "weather_snapshot_id": weather.id if weather else None,
            "coverage": coverage["detail"],
            "boundary_version": geo.boundary_version,
        },
        is_demo=bool(weather.is_demo) if weather else True,
    )
    db.add(snapshot)
    db.flush()

    forecast = Forecast(
        crop_code=crop_code,
        target_code=target_code,
        geo_code=geo_code,
        horizon_days=horizon,
        issue_time=now,
        valid_from=now,
        valid_to=now + timedelta(days=horizon),
        risk_band=risk_band,
        probability=probability,
        confidence_band=confidence,
        coverage=coverage["coverage"],
        coverage_detail=coverage["detail"],
        drivers=drivers,
        reason_code=reason_code,
        model_version=settings.forecast_model_version,
        feature_snapshot_id=snapshot.id,
        boundary_version=geo.boundary_version,
        is_demo=bool(weather.is_demo) if weather else True,
    )
    db.add(forecast)
    run.finished_at = _now()
    run.status = "succeeded"
    run.areas_scored = 1 if reason_code is None else 0
    run.areas_insufficient = 1 if reason_code is not None else 0
    record_audit(
        db,
        action="forecast.generated",
        actor=actor,
        entity_type="forecast",
        entity_id=forecast.id,
        detail={
            "band": risk_band,
            "coverage": coverage["coverage"],
            "reason_code": reason_code,
            "is_demo": forecast.is_demo,
        },
    )
    db.flush()
    return forecast, True


def map_layer(
    db: Session,
    *,
    layer: str,
    bbox: str | None,
    crop: str | None,
    target: str | None,
    date_filter: str | None,
) -> dict:
    settings = get_settings()
    threshold = settings.small_count_threshold
    if layer in {"verified_reports", "unverified_reports"}:
        query = select(Observation, ObservationVerification).join(
            ObservationVerification,
            ObservationVerification.observation_id == Observation.id,
        )
        if crop:
            query = query.where(Observation.crop_code == crop)
        if layer == "verified_reports":
            query = query.where(ObservationVerification.status.in_(["confirmed", "probable"]))
        else:
            query = query.where(
                ObservationVerification.status.in_(["unverified", "pending_review"])
            )
        rows = db.execute(query).all()
        counts: dict[str, int] = {}
        for observation, _verification in rows:
            counts[observation.area_code] = counts.get(observation.area_code, 0) + 1
        return {
            "layer": layer,
            "type": "FeatureCollection",
            "geometry_status": "aggregate_only_no_boundary_geometry",
            "features": [
                {
                    "type": "Feature",
                    "geometry": None,
                    "properties": {
                        "geo_code": code,
                        "count": count if count >= threshold else None,
                        "suppressed": count < threshold,
                        "is_demo": any(
                            observation.is_demo
                            for observation, _ in rows
                            if observation.area_code == code
                        ),
                    },
                }
                for code, count in sorted(counts.items())
            ],
            "legend": "Symbol/count of human-reviewed reports. Empty is not absence.",
        }
    if layer in {"modelled_risk", "coverage"}:
        forecasts = list_forecasts(db, crop=crop, target=target, geo=None, horizon_days=None)[
            "items"
        ]
        features = []
        for item in forecasts:
            if layer == "modelled_risk":
                props = {
                    "geo_code": item["geography"]["code"],
                    "crop": item["crop"],
                    "target": item["target"],
                    "risk_band": item["risk_band"],
                    "coverage": item["coverage"],
                    "issue_time": item["issue_time"],
                    "valid_to": item["valid_to"],
                    "is_stale": item["is_stale"],
                    "is_demo": item["is_demo"],
                }
            else:
                props = {
                    "geo_code": item["geography"]["code"],
                    "coverage": item["coverage"],
                    "coverage_detail": item["coverage_detail"],
                    "issue_time": item["issue_time"],
                    "is_demo": item["is_demo"],
                }
            features.append({"type": "Feature", "geometry": None, "properties": props})
        return {
            "layer": layer,
            "type": "FeatureCollection",
            "geometry_status": "aggregate_only_no_boundary_geometry",
            "features": features,
            "legend": (
                "Modelled area outlook by band; separate from observed reports."
                if layer == "modelled_risk"
                else "How much is known about this area, not how risky it is."
            ),
        }
    if layer == "boundaries":
        rows = db.scalars(select(Geography)).all()
        return {
            "layer": "boundaries",
            "type": "FeatureCollection",
            "geometry_status": "not_available",
            "features": [
                {
                    "type": "Feature",
                    "geometry": None,
                    "properties": {
                        "geo_code": row.code,
                        "level": row.level,
                        "name": row.name,
                        "boundary_version": row.boundary_version,
                    },
                }
                for row in rows
            ],
            "legend": "Versioned admin boundaries. Geometry is not served in this build.",
        }
    raise ApiError(
        404,
        "unknown_layer",
        "Unknown map layer",
        detail="Layers: verified_reports, unverified_reports, modelled_risk, coverage, boundaries",
    )

"""Alert preferences, in-app feed, feedback and admin policy controls."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.core.errors import ApiError
from app.db.models import Forecast, User
from app.db.session import get_db
from app.modules.alerts import service

router = APIRouter(tags=["alerts"])
admin_router = APIRouter(prefix="/admin/alerts", tags=["admin"])


class PreferenceUpdate(BaseModel):
    channel: str
    target_code: str | None = None
    enabled: bool = True
    quiet_start: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    quiet_end: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    language: str | None = None


class FeedbackRequest(BaseModel):
    rating: str
    reason: str | None = Field(default=None, max_length=300)


class PolicyUpdate(BaseModel):
    geo_code: str
    target_code: str
    min_band: str = "high"
    min_coverage: str = "partial"
    cooldown_hours: int = Field(default=24, ge=0, le=720)
    channels: list[str] = Field(default_factory=lambda: ["in_app"])
    active: bool = True


class PauseRequest(BaseModel):
    reason: str = Field(min_length=10, max_length=1000)


class GenerateRequest(BaseModel):
    forecast_id: str


@router.get("/notification-preferences")
def list_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return service.list_preferences(db, user=user)


@router.put("/notification-preferences")
def update_preference(
    payload: PreferenceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    row = service.set_preference(
        db,
        user=user,
        channel=payload.channel,
        target_code=payload.target_code,
        enabled=payload.enabled,
        quiet_start=payload.quiet_start,
        quiet_end=payload.quiet_end,
        language=payload.language,
    )
    db.commit()
    return {
        "channel": row.channel,
        "target_code": row.target_code,
        "enabled": row.enabled,
        "quiet_start": row.quiet_start,
        "quiet_end": row.quiet_end,
        "language": row.language,
    }


@router.get("/alerts")
def list_alerts(
    channel: str = Query(default="in_app", max_length=20),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return service.list_for_user(db, user=user, channel=channel, limit=limit)


@router.post("/alerts/{delivery_id}/feedback", status_code=status.HTTP_201_CREATED)
def add_feedback(
    delivery_id: str,
    payload: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    feedback = service.add_feedback(
        db,
        user=user,
        delivery_id=delivery_id,
        rating=payload.rating,
        reason=payload.reason,
    )
    db.commit()
    return {
        "feedback_id": feedback.id,
        "delivery_id": feedback.delivery_id,
        "rating": feedback.rating,
        "created_at": feedback.created_at.isoformat(),
    }


@admin_router.get("/policies")
def list_policies(
    geo_code: str | None = None,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict:
    return service.list_policies(db, geo_code=geo_code)


@admin_router.put("/policies")
def upsert_policy(
    payload: PolicyUpdate,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict:
    row = service.upsert_policy(
        db,
        actor=user,
        geo_code=payload.geo_code,
        target_code=payload.target_code,
        min_band=payload.min_band,
        min_coverage=payload.min_coverage,
        cooldown_hours=payload.cooldown_hours,
        channels=payload.channels,
        active=payload.active,
    )
    db.commit()
    return {
        "policy_id": row.id,
        "geo_code": row.geo_code,
        "target_code": row.target_code,
        "min_band": row.min_band,
        "min_coverage": row.min_coverage,
        "cooldown_hours": row.cooldown_hours,
        "channels": list(row.channels),
        "active": row.active,
        "approved_by": row.approved_by,
    }


@admin_router.post("/policies/{policy_id}/pause")
def pause_policy(
    policy_id: str,
    payload: PauseRequest,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict:
    row = service.pause_policy(db, actor=user, policy_id=policy_id, reason=payload.reason)
    db.commit()
    return {"policy_id": row.id, "active": row.active, "paused": True}


@admin_router.post("/generate")
def generate_alert(
    payload: GenerateRequest,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict:
    forecast = db.get(Forecast, payload.forecast_id)
    if forecast is None:
        raise ApiError(404, "not_found", "Forecast not found")
    alert, evaluation = service.generate(db, forecast=forecast, actor=user)
    db.commit()
    payload_out: dict = {
        "forecast_id": forecast.id,
        "eligible": evaluation.get("eligible", False),
        "reason_code": evaluation.get("reason_code"),
        "checks": evaluation.get("checks", []),
        "generated": alert is not None and not evaluation.get("deduplicated", False),
        "deduplicated": bool(evaluation.get("deduplicated")),
        "is_update": bool(evaluation.get("is_update")),
    }
    if alert is not None:
        payload_out["alert"] = {
            "alert_id": alert.id,
            "band": alert.band,
            "area_code": alert.geo_code,
            "target_code": alert.target_code,
            "coverage": alert.coverage,
            "window_from": alert.window_from.isoformat(),
            "window_to": alert.window_to.isoformat(),
            "message_version": alert.message_version,
            "notice": service.NOT_CONFIRMATION,
        }
        payload_out["deliveries"] = evaluation.get("deliveries", 0)
    return payload_out


@admin_router.get("/feedback-report")
def feedback_report(
    geo_code: str | None = None,
    target_code: str | None = None,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict:
    return service.feedback_report(db, geo_code=geo_code, target_code=target_code)

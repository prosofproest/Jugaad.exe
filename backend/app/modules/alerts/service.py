"""Area alert policy, generation, delivery and feedback.

Alerts are generated from forecasts only. Every trigger gate is enforced in one
place so a caller cannot skip band, coverage, freshness, advisory, policy or
opt-in checks. Demo forecasts are never promoted to operational alerts.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.db.models import (
    Advisory,
    AdvisoryVersion,
    Alert,
    AlertDelivery,
    AlertFeedback,
    AlertPolicy,
    Forecast,
    Geography,
    NotificationPreference,
    Observation,
    Target,
    User,
    UserAreaAssignment,
)
from app.modules.advisories import service as advisory_service
from app.modules.audit.service import record_audit

BAND_RANK = {"insufficient_data": 0, "low": 1, "moderate": 2, "high": 3, "urgent": 4}
COVERAGE_RANK = {"unknown": 0, "low": 1, "partial": 2, "good": 3}
CHANNELS = {"in_app", "email", "sms"}
DEFAULT_CHANNEL_ENABLED = {"in_app": True, "email": False, "sms": False}
SUPPORTED_CHANNELS = {"in_app"}
FEEDBACK_RATINGS = {"useful", "not_useful", "inaccurate"}
MESSAGE_VERSION = "alert-template-2026-11-v1"
NOT_CONFIRMATION = (
    "This is an early warning, not confirmation of disease in your field."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalise(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _policy_for(db: Session, *, geo_code: str, target_code: str) -> AlertPolicy | None:
    return db.scalar(
        select(AlertPolicy)
        .where(
            AlertPolicy.geo_code == geo_code,
            AlertPolicy.target_code == target_code,
        )
        .order_by(AlertPolicy.created_at.desc())
    )


def evaluate(
    db: Session, *, forecast: Forecast, policy: AlertPolicy | None = None
) -> dict:
    """Evaluate every alert trigger gate without mutating state."""

    checks: list[dict] = []

    if forecast.is_demo:
        return {
            "eligible": False,
            "reason_code": "demo_forecast_excluded",
            "checks": [
                {
                    "gate": "not_demo",
                    "passed": False,
                    "detail": "Demo forecasts are excluded from operational alerts.",
                }
            ],
        }

    now = _now()
    stale = forecast.valid_to < now
    checks.append({"gate": "freshness", "passed": not stale})

    policy = policy or _policy_for(
        db, geo_code=forecast.geo_code, target_code=forecast.target_code
    )
    checks.append(
        {"gate": "policy_active", "passed": bool(policy and policy.active)}
    )

    if policy is None:
        return {
            "eligible": False,
            "reason_code": "policy_missing",
            "checks": checks,
        }

    band_ok = BAND_RANK.get(forecast.risk_band, -1) >= BAND_RANK.get(
        policy.min_band, 99
    )
    checks.append(
        {
            "gate": "risk_band",
            "passed": band_ok,
            "detail": f"{forecast.risk_band} >= {policy.min_band}",
        }
    )

    coverage_ok = COVERAGE_RANK.get(forecast.coverage, -1) >= COVERAGE_RANK.get(
        policy.min_coverage, 99
    )
    checks.append(
        {
            "gate": "coverage",
            "passed": coverage_ok,
            "detail": f"{forecast.coverage} >= {policy.min_coverage}",
        }
    )

    advisory = advisory_service.valid_advisory_for_alert(
        db,
        crop_code=forecast.crop_code,
        target_code=forecast.target_code,
        geo_code=forecast.geo_code,
    )
    checks.append({"gate": "approved_advisory", "passed": advisory is not None})

    failed = [check for check in checks if not check["passed"]]
    if failed:
        first = failed[0]["gate"]
        reason = {
            "freshness": "forecast_stale",
            "policy_active": "policy_inactive",
            "risk_band": "band_below_threshold",
            "coverage": "coverage_below_threshold",
            "approved_advisory": "no_valid_advisory",
        }.get(first, "gate_failed")
        return {
            "eligible": False,
            "reason_code": reason,
            "checks": checks,
            "policy_id": policy.id,
        }

    advisory_row, version = advisory  # type: ignore[misc]
    return {
        "eligible": True,
        "reason_code": None,
        "checks": checks,
        "policy_id": policy.id,
        "advisory_id": advisory_row.id,
        "advisory_version": version.version,
    }


def _dedupe_key(forecast: Forecast) -> str:
    payload = "|".join(
        [
            forecast.geo_code,
            forecast.target_code,
            forecast.risk_band,
            _normalise(forecast.valid_from).isoformat(),
            _normalise(forecast.valid_to).isoformat(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _message_actions(version) -> str:
    actions = list(version.action_types or [])
    return ", ".join(actions) if actions else "scout"


def message_payload(
    db: Session,
    *,
    forecast: Forecast,
    advisory,
    version,
    is_update: bool,
) -> dict:
    geo = db.scalar(select(Geography).where(Geography.code == forecast.geo_code))
    return {
        "template_version": MESSAGE_VERSION,
        "is_update": is_update,
        "area": {"code": forecast.geo_code, "name": geo.name if geo else None},
        "crop": forecast.crop_code,
        "target": forecast.target_code,
        "band": forecast.risk_band,
        "valid_from": _normalise(forecast.valid_from).isoformat(),
        "valid_to": _normalise(forecast.valid_to).isoformat(),
        "reason": ", ".join(list(forecast.drivers or [])) or "no drivers recorded",
        "next_action": _message_actions(version),
        "coverage": forecast.coverage,
        "coverage_detail": forecast.coverage_detail,
        "issue_time": _normalise(forecast.issue_time).isoformat(),
        "advisory_id": advisory.id,
        "advisory_version": version.version,
        "notice": NOT_CONFIRMATION,
        "is_demo": False,
    }


def generate(
    db: Session,
    *,
    forecast: Forecast,
    actor: User | None = None,
) -> tuple[Alert | None, dict]:
    evaluation = evaluate(db, forecast=forecast)
    if not evaluation["eligible"]:
        return None, evaluation

    policy = db.get(AlertPolicy, evaluation["policy_id"])
    advisory = db.get(Advisory, evaluation["advisory_id"])
    if policy is None or advisory is None:
        raise ApiError(409, "alert_state_invalid", "Alert state could not be resolved")
    version = db.get(AdvisoryVersion, advisory.current_version_id)
    if version is None:
        raise ApiError(409, "alert_state_invalid", "Alert state could not be resolved")

    key = _dedupe_key(forecast)
    existing = db.scalar(select(Alert).where(Alert.dedupe_key == key))
    if existing is not None:
        return existing, {
            **evaluation,
            "deduplicated": True,
            "alert_id": existing.id,
        }

    # An escalation within the same measurement window is a new alert with an
    # explicit update label; a downgrade does not create one.
    same_window = db.scalar(
        select(Alert)
        .where(
            Alert.geo_code == forecast.geo_code,
            Alert.target_code == forecast.target_code,
            Alert.window_from == forecast.valid_from,
            Alert.window_to == forecast.valid_to,
        )
        .order_by(Alert.created_at.desc())
    )
    is_update = False
    if same_window is not None:
        if BAND_RANK.get(forecast.risk_band, 0) <= BAND_RANK.get(
            same_window.band, 0
        ):
            return None, {
                **evaluation,
                "eligible": False,
                "reason_code": "downgrade_not_alerted",
                "alert_id": same_window.id,
            }
        is_update = True

    alert = Alert(
        forecast_id=forecast.id,
        geo_code=forecast.geo_code,
        target_code=forecast.target_code,
        band=forecast.risk_band,
        window_from=forecast.valid_from,
        window_to=forecast.valid_to,
        message_version=MESSAGE_VERSION + ("+updated" if is_update else ""),
        coverage=forecast.coverage,
        reason_summary=", ".join(list(forecast.drivers or []))[:300],
        dedupe_key=key,
        is_demo=False,
    )
    db.add(alert)
    db.flush()

    deliveries = dispatch(db, alert=alert, forecast=forecast, policy=policy, version=version)
    record_audit(
        db,
        action="alert.generated",
        actor=actor,
        entity_type="alert",
        entity_id=alert.id,
        detail={
            "forecast_id": forecast.id,
            "band": forecast.risk_band,
            "coverage": forecast.coverage,
            "deliveries": len(deliveries),
            "is_update": is_update,
        },
    )
    return alert, {
        **evaluation,
        "deduplicated": False,
        "alert_id": alert.id,
        "deliveries": len(deliveries),
        "is_update": is_update,
    }


def _recipient_ids(db: Session, alert: Alert) -> list[str]:
    assigned = set(
        db.scalars(
            select(UserAreaAssignment.user_id).where(
                UserAreaAssignment.geo_code == alert.geo_code,
                UserAreaAssignment.active_to.is_(None),
            )
        ).all()
    )
    reporters = set(
        db.scalars(
            select(Observation.user_id).where(
                Observation.area_code == alert.geo_code,
                Observation.deleted_at.is_(None),
            )
        ).all()
    )
    user_ids = assigned | reporters
    if not user_ids:
        return []
    users = db.scalars(
        select(User.id).where(
            User.id.in_(user_ids),
            User.status == "active",
            User.deleted_at.is_(None),
        )
    ).all()
    return list(users)


def _preference(
    db: Session, *, user_id: str, channel: str, target_code: str
) -> NotificationPreference | None:
    return db.scalar(
        select(NotificationPreference)
        .where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.channel == channel,
            or_(
                NotificationPreference.target_code == target_code,
                NotificationPreference.target_code.is_(None),
            ),
        )
        .order_by(
            NotificationPreference.target_code.isnot(None).desc(),
            NotificationPreference.updated_at.desc(),
        )
    )


def _channel_enabled(
    db: Session, *, user_id: str, channel: str, target_code: str
) -> bool:
    pref = _preference(db, user_id=user_id, channel=channel, target_code=target_code)
    if pref is None:
        return DEFAULT_CHANNEL_ENABLED.get(channel, False)
    return pref.enabled


def _in_quiet_hours(pref: NotificationPreference | None, now: datetime) -> bool:
    if pref is None or not pref.quiet_start or not pref.quiet_end:
        return False
    try:
        start_h, start_m = (int(part) for part in pref.quiet_start.split(":"))
        end_h, end_m = (int(part) for part in pref.quiet_end.split(":"))
    except (TypeError, ValueError):
        return False
    current = now.hour * 60 + now.minute
    start = start_h * 60 + start_m
    end = end_h * 60 + end_m
    if start == end:
        return True
    if start < end:
        return start <= current < end
    return current >= start or current < end


def _recent_delivery(
    db: Session, *, user_id: str, alert: Alert, channel: str
) -> tuple[AlertDelivery, Alert] | None:
    row = db.execute(
        select(AlertDelivery, Alert)
        .join(Alert, Alert.id == AlertDelivery.alert_id)
        .where(
            AlertDelivery.user_id == user_id,
            AlertDelivery.channel == channel,
            Alert.geo_code == alert.geo_code,
            Alert.target_code == alert.target_code,
        )
        .order_by(AlertDelivery.created_at.desc())
    ).first()
    return (row[0], row[1]) if row else None


def dispatch(
    db: Session,
    *,
    alert: Alert,
    forecast: Forecast,
    policy: AlertPolicy,
    version,
) -> list[AlertDelivery]:
    now = _now()
    deliveries: list[AlertDelivery] = []
    channels = [channel for channel in policy.channels if channel in CHANNELS]
    if "in_app" not in channels:
        channels.insert(0, "in_app")

    for user_id in _recipient_ids(db, alert):
        for channel in channels:
            pref = _preference(
                db, user_id=user_id, channel=channel, target_code=alert.target_code
            )
            enabled = _channel_enabled(
                db, user_id=user_id, channel=channel, target_code=alert.target_code
            )
            status = "queued"
            reason: str | None = None
            if not enabled:
                status, reason = "opted_out", "opted_out"
            elif channel not in SUPPORTED_CHANNELS:
                status, reason = "suppressed", "channel_not_configured"
            elif channel in {"sms", "email"} and _in_quiet_hours(pref, now):
                status, reason = "suppressed", "quiet_hours"
            else:
                recent = _recent_delivery(
                    db, user_id=user_id, alert=alert, channel=channel
                )
                if recent is not None:
                    previous_delivery, previous_alert = recent
                    within_cooldown = previous_delivery.created_at > now - timedelta(
                        hours=policy.cooldown_hours
                    )
                    escalation = BAND_RANK.get(alert.band, 0) > BAND_RANK.get(
                        previous_alert.band, 0
                    )
                    if within_cooldown and not escalation:
                        status, reason = "suppressed", "cooldown"

            delivery = AlertDelivery(
                alert_id=alert.id,
                user_id=user_id,
                channel=channel,
                status=status,
                sent_at=now if status == "queued" else None,
                suppressed_reason=reason,
            )
            if channel == "in_app" and status == "queued":
                # In-app has no external provider: the row is the delivery.
                delivery.status = "sent"
                delivery.provider_ref = "in_app"
            db.add(delivery)
            deliveries.append(delivery)
    return deliveries


def list_for_user(
    db: Session, *, user: User, channel: str, limit: int = 50
) -> dict:
    query = (
        select(AlertDelivery, Alert)
        .join(Alert, Alert.id == AlertDelivery.alert_id)
        .where(AlertDelivery.user_id == user.id)
        .order_by(AlertDelivery.created_at.desc())
    )
    if channel:
        query = query.where(AlertDelivery.channel == channel)
    rows = db.execute(query.limit(limit)).all()
    items = []
    for delivery, alert in rows:
        forecast = db.get(Forecast, alert.forecast_id)
        items.append(
            {
                "delivery_id": delivery.id,
                "alert_id": alert.id,
                "channel": delivery.channel,
                "delivery_status": delivery.status,
                "suppressed_reason": delivery.suppressed_reason,
                "band": alert.band,
                "area_code": alert.geo_code,
                "target_code": alert.target_code,
                "window_from": _normalise(alert.window_from).isoformat(),
                "window_to": _normalise(alert.window_to).isoformat(),
                "coverage": alert.coverage,
                "reason_summary": alert.reason_summary,
                "message_version": alert.message_version,
                "issue_time": _normalise(forecast.issue_time).isoformat()
                if forecast
                else None,
                "notice": NOT_CONFIRMATION,
                "is_demo": alert.is_demo,
            }
        )
    return {"items": items, "channel": channel}


def add_feedback(
    db: Session, *, user: User, delivery_id: str, rating: str, reason: str | None
) -> AlertFeedback:
    if rating not in FEEDBACK_RATINGS:
        raise ApiError(
            422,
            "invalid_rating",
            "Rating must be useful, not_useful or inaccurate",
        )
    delivery = db.get(AlertDelivery, delivery_id)
    if delivery is None or delivery.user_id != user.id:
        raise ApiError(404, "not_found", "Alert delivery not found")
    feedback = AlertFeedback(
        delivery_id=delivery.id,
        rating=rating,
        reason=reason[:300] if reason else None,
    )
    db.add(feedback)
    record_audit(
        db,
        action="alert.feedback_recorded",
        actor=user,
        entity_type="alert_delivery",
        entity_id=delivery.id,
        detail={"rating": rating},
    )
    return feedback


def list_preferences(db: Session, *, user: User) -> dict:
    rows = db.scalars(
        select(NotificationPreference)
        .where(NotificationPreference.user_id == user.id)
        .order_by(NotificationPreference.channel)
    ).all()
    return {
        "items": [
            {
                "channel": row.channel,
                "target_code": row.target_code,
                "enabled": row.enabled,
                "quiet_start": row.quiet_start,
                "quiet_end": row.quiet_end,
                "language": row.language,
                "updated_at": row.updated_at.isoformat(),
            }
            for row in rows
        ],
        "channels": {
            "in_app": "always available unless explicitly opted out",
            "email": "staff opt-in; not configured for farmers",
            "sms": "optional channel; adapter interface only until a gateway is approved",
        },
    }


def set_preference(
    db: Session,
    *,
    user: User,
    channel: str,
    target_code: str | None,
    enabled: bool,
    quiet_start: str | None,
    quiet_end: str | None,
    language: str | None,
) -> NotificationPreference:
    if channel not in CHANNELS:
        raise ApiError(422, "invalid_channel", "Unknown notification channel")
    if language is not None and language not in {"en", "kn"}:
        raise ApiError(422, "unsupported_language", "Supported languages are en and kn")
    if target_code:
        target = db.scalar(select(Target).where(Target.code == target_code))
        if target is None:
            raise ApiError(422, "unknown_target", "Target is not in the allowlist")
    row = db.scalar(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user.id,
            NotificationPreference.channel == channel,
            (
                NotificationPreference.target_code == target_code
                if target_code
                else NotificationPreference.target_code.is_(None)
            ),
        )
    )
    if row is None:
        row = NotificationPreference(
            user_id=user.id,
            channel=channel,
            target_code=target_code,
            enabled=enabled,
            quiet_start=quiet_start,
            quiet_end=quiet_end,
            language=language or user.locale,
        )
        db.add(row)
    else:
        row.enabled = enabled
        row.quiet_start = quiet_start
        row.quiet_end = quiet_end
        if language:
            row.language = language
        row.updated_at = _now()
    record_audit(
        db,
        action="alert.preference_changed",
        actor=user,
        entity_type="notification_preference",
        entity_id=row.id,
        detail={"channel": channel, "target_code": target_code, "enabled": enabled},
    )
    return row


# ---------------------------------------------------------------------------
# Admin policy management
# ---------------------------------------------------------------------------
def list_policies(db: Session, *, geo_code: str | None = None) -> dict:
    query = select(AlertPolicy)
    if geo_code:
        query = query.where(AlertPolicy.geo_code == geo_code)
    rows = db.scalars(query.order_by(AlertPolicy.created_at.desc())).all()
    return {
        "items": [
            {
                "policy_id": row.id,
                "geo_code": row.geo_code,
                "target_code": row.target_code,
                "min_band": row.min_band,
                "min_coverage": row.min_coverage,
                "cooldown_hours": row.cooldown_hours,
                "channels": list(row.channels),
                "approved_by": row.approved_by,
                "active": row.active,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }


def upsert_policy(
    db: Session,
    *,
    actor: User,
    geo_code: str,
    target_code: str,
    min_band: str,
    min_coverage: str,
    cooldown_hours: int,
    channels: list[str],
    active: bool,
) -> AlertPolicy:
    if db.scalar(select(Geography).where(Geography.code == geo_code)) is None:
        raise ApiError(422, "unknown_area", "Area code is not recognised")
    target = db.scalar(select(Target).where(Target.code == target_code))
    if target is None:
        raise ApiError(422, "unknown_target", "Target is not in the allowlist")
    if min_band not in BAND_RANK or min_band == "insufficient_data":
        raise ApiError(422, "invalid_band", "Unknown minimum risk band")
    if min_coverage not in COVERAGE_RANK:
        raise ApiError(422, "invalid_coverage", "Unknown minimum coverage")
    unknown = sorted(set(channels) - CHANNELS)
    if unknown:
        raise ApiError(422, "invalid_channel", f"Unknown channel: {unknown[0]}")
    if cooldown_hours < 0 or cooldown_hours > 720:
        raise ApiError(422, "invalid_cooldown", "Cooldown must be between 0 and 720 hours")
    row = _policy_for(db, geo_code=geo_code, target_code=target_code)
    if row is None:
        row = AlertPolicy(
            geo_code=geo_code,
            target_code=target_code,
            min_band=min_band,
            min_coverage=min_coverage,
            cooldown_hours=cooldown_hours,
            channels=channels or ["in_app"],
            approved_by=actor.id,
            active=active,
        )
        db.add(row)
    else:
        row.min_band = min_band
        row.min_coverage = min_coverage
        row.cooldown_hours = cooldown_hours
        row.channels = channels or ["in_app"]
        row.active = active
        row.approved_by = actor.id
    record_audit(
        db,
        action="alert.policy_changed",
        actor=actor,
        entity_type="alert_policy",
        entity_id=row.id,
        detail={"active": active, "min_band": min_band, "min_coverage": min_coverage},
    )
    return row


def pause_policy(db: Session, *, actor: User, policy_id: str, reason: str) -> AlertPolicy:
    row = db.get(AlertPolicy, policy_id)
    if row is None:
        raise ApiError(404, "not_found", "Alert policy not found")
    row.active = False
    record_audit(
        db,
        action="alert.policy_paused",
        actor=actor,
        entity_type="alert_policy",
        entity_id=row.id,
        reason=reason,
    )
    return row


def feedback_report(
    db: Session, *, geo_code: str | None, target_code: str | None
) -> dict:
    query = (
        select(
            AlertFeedback.rating,
            func.count(AlertFeedback.id),
        )
        .join(AlertDelivery, AlertDelivery.id == AlertFeedback.delivery_id)
        .join(Alert, Alert.id == AlertDelivery.alert_id)
        .group_by(AlertFeedback.rating)
    )
    if geo_code:
        query = query.where(Alert.geo_code == geo_code)
    if target_code:
        query = query.where(Alert.target_code == target_code)
    rows = db.execute(query).all()
    return {
        "items": [{"rating": rating, "count": count} for rating, count in rows],
        "filters": {"geo_code": geo_code, "target_code": target_code},
    }

"""Alert trigger policy (spec 07 §5, FR-07-05/06/09).

All gates must pass. The function is pure: it reads a forecast snapshot, an
approved policy, an approved advisory and the current preferences, and returns
a reason code plus the eligible recipient ids.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict

from app.modules.advisories.models import ALL_SUPPORTED_AREAS, ApprovedAdvisoryView
from app.modules.alerts.models import (
    BAND_ORDER,
    AlertPolicy,
    ForecastSnapshot,
    NotificationPreference,
)


class TriggerResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    triggered: bool
    reason: str
    recipients: tuple[str, ...] = ()


def dedupe_key(
    *,
    geo_code: str,
    target_code: str,
    band: str,
    window_from: AwareDatetime,
    window_to: AwareDatetime,
) -> str:
    payload = {
        "geo_code": geo_code,
        "target_code": target_code,
        "band": band,
        "window_from": window_from.isoformat(),
        "window_to": window_to.isoformat(),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def eligible_recipients(
    *,
    forecast: ForecastSnapshot,
    policy: AlertPolicy,
    advisory: ApprovedAdvisoryView,
    preferences: tuple[NotificationPreference, ...],
) -> tuple[str, ...]:
    recipients: list[str] = []
    policy_channels = set(policy.channels)
    for preference in preferences:
        if preference.geo_code != forecast.geo_code:
            continue
        if preference.language != advisory.language:
            continue
        if forecast.target_code in preference.opted_out_targets:
            continue
        if not (set(preference.channels) & policy_channels):
            continue
        recipients.append(preference.user_id)
    return tuple(sorted(set(recipients)))


def evaluate_trigger(
    *,
    forecast: ForecastSnapshot,
    policy: AlertPolicy,
    advisory: ApprovedAdvisoryView | None,
    preferences: tuple[NotificationPreference, ...],
    paused: bool,
    now: datetime,
) -> TriggerResult:
    if policy.geo_code != forecast.geo_code or policy.target_code != forecast.target_code:
        return TriggerResult(triggered=False, reason="policy_scope_mismatch")
    if forecast.is_demo:
        return TriggerResult(triggered=False, reason="demo_forecast")
    if paused:
        return TriggerResult(triggered=False, reason="paused")
    if not policy.active:
        return TriggerResult(triggered=False, reason="policy_inactive")
    if forecast.is_stale:
        return TriggerResult(triggered=False, reason="stale_forecast")
    if forecast.band == "insufficient":
        return TriggerResult(triggered=False, reason="insufficient_band")
    if BAND_ORDER[forecast.band] < BAND_ORDER[policy.min_band]:
        return TriggerResult(triggered=False, reason="band_below_minimum")
    if forecast.coverage < policy.min_coverage:
        return TriggerResult(triggered=False, reason="low_coverage")
    if not forecast.drivers:
        return TriggerResult(triggered=False, reason="missing_reason_codes")
    if advisory is None:
        return TriggerResult(triggered=False, reason="advisory_unavailable")
    if advisory.crop_code != forecast.crop_code or advisory.target_code != forecast.target_code:
        return TriggerResult(triggered=False, reason="advisory_scope_mismatch")
    if ALL_SUPPORTED_AREAS not in advisory.geo_scope and (
        forecast.geo_code not in advisory.geo_scope
    ):
        return TriggerResult(triggered=False, reason="advisory_scope_mismatch")
    if not (advisory.valid_from <= now < advisory.valid_to):
        return TriggerResult(triggered=False, reason="advisory_expired")

    recipients = eligible_recipients(
        forecast=forecast,
        policy=policy,
        advisory=advisory,
        preferences=preferences,
    )
    if not recipients:
        return TriggerResult(triggered=False, reason="no_opted_in_recipients")
    return TriggerResult(triggered=True, reason="triggered", recipients=recipients)

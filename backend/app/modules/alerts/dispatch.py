"""Alert generation, persistence and bounded dispatch (spec 07 §5–§7).

The service has no production provider. A deployment injects one, and until it
does every attempted delivery is recorded as ``failed`` with
``provider_not_configured``. That is deliberate: a missing provider must never
look like a successful send.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import RLock
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from app.core.audit import AuditEvent, AuditLog
from app.modules.advisories.models import ApprovedAdvisoryView
from app.modules.advisories.registry import AdvisoryRegistry
from app.modules.alerts.models import (
    BAND_ORDER,
    RECEIVED_STATUSES,
    Alert,
    AlertDelivery,
    AlertFeedback,
    AlertPolicy,
    FeedbackSummary,
    ForecastSnapshot,
    InboxItem,
    NotificationPreference,
    ProviderReceipt,
    RenderedMessage,
)
from app.modules.alerts.templates import TemplateError, TemplateRegistry, render_alert
from app.modules.alerts.trigger import dedupe_key, evaluate_trigger

Clock = Callable[[], datetime]
Sleeper = Callable[[float], None]


class FeedbackError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ProviderNotConfigured(Exception):
    def __init__(self, code: str = "provider_not_configured") -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Recipient:
    user_id: str
    language: str


class DeliveryProvider(Protocol):
    def send(self, message: RenderedMessage, recipient: Recipient) -> ProviderReceipt:
        """Return a receipt. Never claim ``sent`` when the provider did not accept it."""


class DispatchResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    triggered: bool
    reason: str
    alert: Alert | None = None
    recipients: tuple[str, ...] = ()
    deduplicated: bool = False


@dataclass
class _PauseState:
    geo_code: str
    target_code: str
    actor_id: str
    reason: str
    paused_at: datetime


class AlertService:
    def __init__(
        self,
        *,
        advisory_registry: AdvisoryRegistry,
        template_registry: TemplateRegistry,
        provider: DeliveryProvider | None = None,
        clock: Clock | None = None,
        retry_attempts: int = 2,
        retry_backoff_s: float = 0.0,
        sleep: Sleeper | None = None,
    ) -> None:
        if retry_attempts < 1:
            raise ValueError("retry_attempts must be at least 1")
        if retry_backoff_s < 0:
            raise ValueError("retry_backoff_s must not be negative")
        self._advisories = advisory_registry
        self._templates = template_registry
        self._provider = provider
        self._clock = clock if clock is not None else (lambda: datetime.now().astimezone())
        self._retry_attempts = retry_attempts
        self._retry_backoff_s = retry_backoff_s
        self._sleep = sleep if sleep is not None else time.sleep

        self._alerts_by_key: dict[str, Alert] = {}
        self._alerts_by_id: dict[str, Alert] = {}
        self._order: list[str] = []
        self._preferences: dict[str, NotificationPreference] = {}
        self._paused: dict[tuple[str, str], _PauseState] = {}
        self._feedback: list[AlertFeedback] = []
        self._delivery_to_alert: dict[str, str] = {}
        self._audit = AuditLog(self._clock)
        self._lock = RLock()

    # ----------------------------------------------------------- preferences

    def set_preference(self, preference: NotificationPreference) -> None:
        with self._lock:
            self._preferences[preference.user_id] = preference
        self._audit.record(
            "alert.preference_updated",
            entity_type="notification_preference",
            entity_id=preference.user_id,
            actor_id=preference.user_id,
            detail={
                "geo_code": preference.geo_code,
                "channels": ",".join(preference.channels),
                "opted_out_targets": ",".join(preference.opted_out_targets),
                "language": preference.language,
            },
        )

    def get_preference(self, user_id: str) -> NotificationPreference | None:
        with self._lock:
            return self._preferences.get(user_id)

    # --------------------------------------------------------------- control

    def pause(self, *, geo_code: str, target_code: str, actor_id: str, reason: str) -> None:
        if not reason.strip():
            raise ValueError("pause reason is required")
        with self._lock:
            self._paused[(geo_code, target_code)] = _PauseState(
                geo_code=geo_code,
                target_code=target_code,
                actor_id=actor_id,
                reason=reason.strip(),
                paused_at=self._clock(),
            )
        self._audit.record(
            "alert.paused",
            entity_type="alert_scope",
            entity_id=f"{geo_code}:{target_code}",
            actor_id=actor_id,
            detail={"reason": reason.strip()},
        )

    def resume(self, *, geo_code: str, target_code: str, actor_id: str) -> None:
        with self._lock:
            self._paused.pop((geo_code, target_code), None)
        self._audit.record(
            "alert.resumed",
            entity_type="alert_scope",
            entity_id=f"{geo_code}:{target_code}",
            actor_id=actor_id,
        )

    def is_paused(self, geo_code: str, target_code: str) -> bool:
        with self._lock:
            return (geo_code, target_code) in self._paused

    # -------------------------------------------------------------- dispatch

    def dispatch(
        self,
        *,
        forecast: ForecastSnapshot,
        policy: AlertPolicy,
        language: str,
    ) -> DispatchResult:
        now = self._clock()
        key = dedupe_key(
            geo_code=forecast.geo_code,
            target_code=forecast.target_code,
            band=forecast.band,
            window_from=forecast.window_from,
            window_to=forecast.window_to,
        )

        with self._lock:
            existing = self._alerts_by_key.get(key)
            if existing is not None:
                return DispatchResult(
                    triggered=True,
                    reason="duplicate",
                    alert=existing,
                    deduplicated=True,
                )
            prior = self._prior_alert(forecast)
            if prior is not None and BAND_ORDER[forecast.band] < BAND_ORDER[prior.band]:
                self._audit.record(
                    "alert.downgrade_suppressed",
                    entity_type="forecast",
                    entity_id=forecast.forecast_id,
                    detail={"prior_band": prior.band, "new_band": forecast.band},
                )
                return DispatchResult(triggered=False, reason="downgrade", alert=prior)
            paused = (forecast.geo_code, forecast.target_code) in self._paused
            preferences = tuple(self._preferences.values())

        result = self._advisories.retrieve(
            crop=forecast.crop_code,
            target=forecast.target_code,
            geo=forecast.geo_code,
            language=language,
            now=now,
        )
        advisory = result.items[0] if result.items else None
        trigger = evaluate_trigger(
            forecast=forecast,
            policy=policy,
            advisory=advisory,
            preferences=preferences,
            paused=paused,
            now=now,
        )
        if not trigger.triggered or advisory is None:
            self._audit.record(
                "alert.skipped",
                entity_type="forecast",
                entity_id=forecast.forecast_id,
                detail={"reason": trigger.reason},
            )
            return DispatchResult(triggered=False, reason=trigger.reason)

        updated = prior is not None and BAND_ORDER[forecast.band] > BAND_ORDER[prior.band]
        alert_id = f"alert_{uuid4().hex}"
        deliveries = self._build_deliveries(
            alert_id=alert_id,
            forecast=forecast,
            policy=policy,
            advisory=advisory,
            preferences=preferences,
            updated=updated,
            now=now,
        )
        if not deliveries:
            return DispatchResult(triggered=False, reason="no_opted_in_recipients")

        all_suppressed = all(item.status == "suppressed" for item in deliveries)
        alert = Alert(
            alert_id=alert_id,
            forecast_id=forecast.forecast_id,
            geo_code=forecast.geo_code,
            crop_code=forecast.crop_code,
            target_code=forecast.target_code,
            band=forecast.band,  # type: ignore[arg-type]
            coverage=forecast.coverage,
            window_from=forecast.window_from,
            window_to=forecast.window_to,
            issued_at=forecast.issued_at,
            generated_at=now,
            dedupe_key=key,
            updated=updated,
            suppressed=all_suppressed,
            suppression_reason="cooldown" if all_suppressed else None,
            advisory_id=advisory.advisory_id,
            advisory_version=advisory.version,
            message_version=policy.template_version,
            deliveries=tuple(deliveries),
        )

        # Persist before dispatch so a provider failure cannot erase the alert.
        with self._lock:
            self._alerts_by_key[key] = alert
            self._alerts_by_id[alert_id] = alert
            self._order.append(alert_id)
            for delivery in deliveries:
                self._delivery_to_alert[delivery.delivery_id] = alert_id
        self._audit.record(
            "alert.generated",
            entity_type="alert",
            entity_id=alert_id,
            detail={
                "band": forecast.band,
                "recipients": len(trigger.recipients),
                "suppressed": all_suppressed,
            },
        )
        for delivery in deliveries:
            if delivery.status == "suppressed":
                self._audit.record(
                    "alert.delivery_suppressed",
                    entity_type="alert_delivery",
                    entity_id=delivery.delivery_id,
                    actor_id=delivery.user_id,
                    detail={"reason": delivery.suppression_reason or "cooldown"},
                )

        final_deliveries = tuple(
            self._send(
                delivery=delivery,
                forecast=forecast,
                language=language,
                updated=updated,
            )
            if delivery.status == "queued"
            else delivery
            for delivery in deliveries
        )
        final = alert.model_copy(update={"deliveries": final_deliveries})
        with self._lock:
            self._alerts_by_id[alert_id] = final
            self._alerts_by_key[key] = final

        received = any(item.status in RECEIVED_STATUSES for item in final_deliveries)
        failed = any(item.status == "failed" for item in final_deliveries)
        reason = (
            "triggered" if received else ("suppressed" if all_suppressed else "delivery_failed")
        )
        if failed and not received and not all_suppressed:
            reason = "delivery_failed"
        return DispatchResult(
            triggered=True,
            reason=reason,
            alert=final,
            recipients=trigger.recipients,
        )

    # ---------------------------------------------------------------- reads

    def get_alert(self, alert_id: str) -> Alert | None:
        with self._lock:
            return self._alerts_by_id.get(alert_id)

    def history(
        self,
        *,
        geo_code: str | None = None,
        target_code: str | None = None,
    ) -> list[Alert]:
        with self._lock:
            alerts = [self._alerts_by_id[item] for item in reversed(self._order)]
        if geo_code is not None:
            alerts = [item for item in alerts if item.geo_code == geo_code]
        if target_code is not None:
            alerts = [item for item in alerts if item.target_code == target_code]
        return alerts

    def inbox(self, user_id: str, *, limit: int = 20, cursor: str | None = None) -> list[InboxItem]:
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        offset = 0
        if cursor is not None:
            try:
                offset = int(cursor)
            except ValueError as error:
                raise ValueError("invalid cursor") from error
            if offset < 0:
                raise ValueError("invalid cursor")

        with self._lock:
            alerts = [self._alerts_by_id[item] for item in reversed(self._order)]
        items: list[InboxItem] = []
        for alert in alerts:
            for delivery in alert.deliveries:
                if delivery.user_id != user_id:
                    continue
                if delivery.status not in RECEIVED_STATUSES:
                    continue
                items.append(
                    InboxItem(
                        alert_id=alert.alert_id,
                        delivery_id=delivery.delivery_id,
                        geo_code=alert.geo_code,
                        crop_code=alert.crop_code,
                        target_code=alert.target_code,
                        band=alert.band,
                        window_from=alert.window_from,
                        window_to=alert.window_to,
                        generated_at=alert.generated_at,
                        channel=delivery.channel,
                        status=delivery.status,  # type: ignore[arg-type]
                        message_text=delivery.message_text,
                        suppression_reason=delivery.suppression_reason,
                    )
                )
        return items[offset : offset + limit]

    # --------------------------------------------------------------- feedback

    def submit_feedback(
        self,
        *,
        delivery_id: str,
        user_id: str,
        rating: str,
        reason: str | None = None,
    ) -> AlertFeedback:
        if rating not in {"useful", "not_useful", "inaccurate"}:
            raise FeedbackError("invalid_rating")
        with self._lock:
            alert_id = self._delivery_to_alert.get(delivery_id)
            if alert_id is None:
                raise FeedbackError("delivery_not_found")
            alert = self._alerts_by_id[alert_id]
            delivery = next(
                (item for item in alert.deliveries if item.delivery_id == delivery_id),
                None,
            )
        if delivery is None:
            raise FeedbackError("delivery_not_found")
        if delivery.user_id != user_id:
            raise FeedbackError("not_owner")
        if delivery.status not in RECEIVED_STATUSES:
            raise FeedbackError("delivery_not_received")

        feedback = AlertFeedback(
            feedback_id=f"fb_{uuid4().hex}",
            delivery_id=delivery_id,
            user_id=user_id,
            rating=rating,  # type: ignore[arg-type]
            reason=reason,
            created_at=self._clock(),
        )
        with self._lock:
            self._feedback.append(feedback)
        self._audit.record(
            "alert.feedback_recorded",
            entity_type="alert_delivery",
            entity_id=delivery_id,
            actor_id=user_id,
            detail={"rating": rating},
        )
        return feedback

    def feedback_summary(
        self,
        *,
        geo_code: str | None = None,
        target_code: str | None = None,
        band: str | None = None,
    ) -> FeedbackSummary:
        counts = {"useful": 0, "not_useful": 0, "inaccurate": 0}
        with self._lock:
            feedback = list(self._feedback)
            alerts = dict(self._alerts_by_id)
        for item in feedback:
            alert_id = self._delivery_to_alert.get(item.delivery_id)
            if alert_id is None:
                continue
            alert = alerts.get(alert_id)
            if alert is None:
                continue
            if geo_code is not None and alert.geo_code != geo_code:
                continue
            if target_code is not None and alert.target_code != target_code:
                continue
            if band is not None and alert.band != band:
                continue
            counts[item.rating] += 1
        return FeedbackSummary(counts=counts, total=sum(counts.values()))

    def audit_events(self) -> list[AuditEvent]:
        return self._audit.events()

    # ------------------------------------------------------------- internals

    def _prior_alert(self, forecast: ForecastSnapshot) -> Alert | None:
        matches = [
            alert
            for alert in self._alerts_by_id.values()
            if alert.geo_code == forecast.geo_code
            and alert.target_code == forecast.target_code
            and alert.window_from == forecast.window_from
            and alert.window_to == forecast.window_to
        ]
        if not matches:
            return None
        return max(matches, key=lambda item: (BAND_ORDER[item.band], item.generated_at))

    def _build_deliveries(
        self,
        *,
        alert_id: str,
        forecast: ForecastSnapshot,
        policy: AlertPolicy,
        advisory: ApprovedAdvisoryView,
        preferences: tuple[NotificationPreference, ...],
        updated: bool,
        now: datetime,
    ) -> list[AlertDelivery]:
        by_user = {item.user_id: item for item in preferences}
        deliveries: list[AlertDelivery] = []
        cooldown = timedelta(hours=policy.cooldowns[forecast.band])

        for user_id in sorted(by_user):
            preference = by_user[user_id]
            if preference.geo_code != forecast.geo_code:
                continue
            if preference.language != advisory.language:
                continue
            if forecast.target_code in preference.opted_out_targets:
                continue
            for channel in policy.channels:
                if channel not in preference.channels:
                    continue
                delivery_id = f"del_{uuid4().hex}"
                try:
                    template = self._templates.require(channel, policy.template_version)
                    message = render_alert(
                        template=template,
                        forecast=forecast,
                        advisory=advisory,
                        updated=updated,
                    )
                except TemplateError as error:
                    deliveries.append(
                        AlertDelivery(
                            delivery_id=delivery_id,
                            alert_id=alert_id,
                            user_id=user_id,
                            channel=channel,
                            status="failed",
                            error=error.code,
                            queued_at=now,
                            advisory_id=advisory.advisory_id,
                            advisory_version=advisory.version,
                        )
                    )
                    continue

                last = self._last_received(
                    user_id=user_id,
                    geo_code=forecast.geo_code,
                    target_code=forecast.target_code,
                    channel=channel,
                )
                if last is not None and now - last < cooldown:
                    deliveries.append(
                        AlertDelivery(
                            delivery_id=delivery_id,
                            alert_id=alert_id,
                            user_id=user_id,
                            channel=channel,
                            status="suppressed",
                            queued_at=now,
                            suppression_reason="cooldown",
                            message_version=message.template_version,
                            message_text=message.text,
                            advisory_id=advisory.advisory_id,
                            advisory_version=advisory.version,
                        )
                    )
                    continue

                deliveries.append(
                    AlertDelivery(
                        delivery_id=delivery_id,
                        alert_id=alert_id,
                        user_id=user_id,
                        channel=channel,
                        status="queued",
                        queued_at=now,
                        message_version=message.template_version,
                        message_text=message.text,
                        advisory_id=advisory.advisory_id,
                        advisory_version=advisory.version,
                    )
                )
        return deliveries

    def _send(
        self,
        *,
        delivery: AlertDelivery,
        forecast: ForecastSnapshot,
        language: str,
        updated: bool,
    ) -> AlertDelivery:
        message = RenderedMessage(
            channel=delivery.channel,
            template_version=delivery.message_version or "unknown",
            text=delivery.message_text or "",
            updated=updated,
        )
        recipient = Recipient(user_id=delivery.user_id, language=language)

        if self._provider is None:
            self._audit.record(
                "alert.delivery_failed",
                entity_type="alert_delivery",
                entity_id=delivery.delivery_id,
                actor_id=delivery.user_id,
                detail={"reason": "provider_not_configured"},
            )
            return delivery.model_copy(
                update={
                    "status": "failed",
                    "error": "provider_not_configured",
                    "attempt_count": 0,
                }
            )

        attempts = 0
        last_error = "provider_error"
        while attempts < self._retry_attempts:
            attempts += 1
            receipt: ProviderReceipt | None = None
            try:
                receipt = self._provider.send(message, recipient)
            except ProviderNotConfigured as error:
                last_error = error.code
            except Exception:  # noqa: BLE001 - provider boundary converts every failure
                last_error = "provider_error"

            if receipt is not None and receipt.status in RECEIVED_STATUSES:
                at = self._clock()
                self._audit.record(
                    "alert.delivery_sent",
                    entity_type="alert_delivery",
                    entity_id=delivery.delivery_id,
                    actor_id=delivery.user_id,
                    detail={"channel": delivery.channel, "status": receipt.status},
                )
                return delivery.model_copy(
                    update={
                        "status": receipt.status,
                        "provider_ref": receipt.provider_ref,
                        "attempt_count": attempts,
                        "sent_at": at,
                        "delivered_at": at if receipt.status == "delivered" else None,
                        "error": None,
                    }
                )
            if receipt is not None and receipt.error:
                last_error = receipt.error
            if attempts < self._retry_attempts and self._retry_backoff_s > 0:
                self._sleep(self._retry_backoff_s * (2 ** (attempts - 1)))

        self._audit.record(
            "alert.delivery_failed",
            entity_type="alert_delivery",
            entity_id=delivery.delivery_id,
            actor_id=delivery.user_id,
            detail={"channel": delivery.channel, "reason": last_error},
        )
        return delivery.model_copy(
            update={
                "status": "failed",
                "error": last_error,
                "attempt_count": attempts,
            }
        )

    def _last_received(
        self,
        *,
        user_id: str,
        geo_code: str,
        target_code: str,
        channel: str,
    ) -> datetime | None:
        latest: datetime | None = None
        with self._lock:
            alerts = list(self._alerts_by_id.values())
        for alert in alerts:
            if alert.geo_code != geo_code or alert.target_code != target_code:
                continue
            for delivery in alert.deliveries:
                if delivery.user_id != user_id or delivery.channel != channel:
                    continue
                if delivery.status not in RECEIVED_STATUSES:
                    continue
                at = delivery.sent_at or delivery.delivered_at or delivery.queued_at
                if latest is None or at > latest:
                    latest = at
        return latest

"""Synthetic fixtures for advisory and alert tests.

Everything here is a labelled test fixture: no crop, target, geography, wording
or threshold is a production decision.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from app.modules.advisories.models import AdvisoryBody, AdvisoryDraft
from app.modules.advisories.registry import AdvisoryRegistry
from app.modules.alerts.dispatch import AlertService, Recipient
from app.modules.alerts.models import (
    AlertPolicy,
    ForecastSnapshot,
    NotificationPreference,
    ProviderReceipt,
    RenderedMessage,
)
from app.modules.alerts.templates import AlertTemplate, TemplateRegistry

NOW = datetime(2026, 11, 6, 8, 0, 0, tzinfo=UTC)
QUALIFIED_ACCOUNTS = {
    "author-1": "agronomist",
    "approver-1": "pathologist",
    "approver-2": "agronomist",
}


class MutableClock:
    def __init__(self, now: datetime = NOW) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs: float) -> None:
        self.now = self.now + timedelta(**kwargs)


def make_body(**overrides: str) -> AdvisoryBody:
    values = {
        "what_this_is_about": (
            "Leaf spotting on the supported crop in the defined area and time window."
        ),
        "what_you_may_see": ("Small dark spots on leaves; leaves may yellow around the spots."),
        "what_to_do_now": (
            "Inspect plants across the field and keep a photo record for comparison."
        ),
        "what_not_to_assume": (
            "This is not a diagnosis and does not confirm an outbreak in your field."
        ),
        "when_to_escalate": (
            "Request expert review if symptoms spread quickly or affect many plants."
        ),
        "source_and_approval": "Synthetic test fixture approved by the test agronomist.",
    }
    values.update(overrides)
    return AdvisoryBody(**values)


def make_draft(
    *,
    crop_code: str = "crop-1",
    target_code: str = "target-1",
    geo_scope: list[str] | None = None,
    language: str = "en",
    title: str = "Synthetic leaf spotting advisory",
    body: AdvisoryBody | None = None,
    action_types: list[str] | None = None,
    valid_from: datetime = NOW - timedelta(days=1),
    valid_to: datetime = NOW + timedelta(days=30),
    author_id: str = "author-1",
    author_role: str = "agronomist",
) -> AdvisoryDraft:
    return AdvisoryDraft.model_validate(
        {
            "crop_code": crop_code,
            "target_code": target_code,
            "geo_scope": geo_scope or ["area-1"],
            "language": language,
            "title": title,
            "body": body or make_body(),
            "action_types": action_types or ["scout", "record"],
            "source": "Synthetic test source",
            "valid_from": valid_from,
            "valid_to": valid_to,
            "author_id": author_id,
            "author_role": author_role,
        }
    )


def populate_advisory(
    registry: AdvisoryRegistry,
    *,
    draft: AdvisoryDraft | None = None,
    approver_id: str = "approver-1",
    approver_role: str = "pathologist",
    accounts: dict[str, str] | None = None,
) -> str:
    advisory = registry.create_draft(draft or make_draft())
    registry.approve(
        advisory.advisory_id,
        version=1,
        approver_id=approver_id,
        approver_role=approver_role,
        qualified_accounts=accounts or QUALIFIED_ACCOUNTS,
    )
    registry.publish(advisory.advisory_id, version=1, actor_id="publisher-1")
    return advisory.advisory_id


def make_policy(
    *,
    geo_code: str = "area-1",
    target_code: str = "target-1",
    min_band: str = "moderate",
    min_coverage: float = 0.6,
    channels: tuple[str, ...] = ("sms", "push"),
    template_version: str = "tpl-1",
    cooldowns: dict[str, float] | None = None,
    active: bool = True,
) -> AlertPolicy:
    return AlertPolicy.model_validate(
        {
            "policy_id": "policy-1",
            "geo_code": geo_code,
            "target_code": target_code,
            "min_band": min_band,
            "min_coverage": min_coverage,
            "cooldowns": cooldowns or {"low": 24.0, "moderate": 24.0, "high": 24.0, "urgent": 24.0},
            "channels": channels,
            "template_version": template_version,
            "approved_by": "agronomist-1",
            "approved_at": NOW - timedelta(days=1),
            "active": active,
        }
    )


def make_forecast(
    *,
    forecast_id: str = "forecast-1",
    geo_code: str = "area-1",
    crop_code: str = "crop-1",
    target_code: str = "target-1",
    band: str = "high",
    coverage: float = 0.8,
    is_stale: bool = False,
    is_demo: bool = False,
    window_from: datetime = NOW - timedelta(days=1),
    window_to: datetime = NOW + timedelta(days=7),
    drivers: tuple[str, ...] = ("humidity", "rainfall"),
) -> ForecastSnapshot:
    return ForecastSnapshot.model_validate(
        {
            "forecast_id": forecast_id,
            "crop_code": crop_code,
            "target_code": target_code,
            "geo_code": geo_code,
            "band": band,
            "coverage": coverage,
            "is_stale": is_stale,
            "is_demo": is_demo,
            "window_from": window_from,
            "window_to": window_to,
            "issued_at": NOW,
            "drivers": drivers,
        }
    )


def make_preference(
    *,
    user_id: str = "user-1",
    geo_code: str = "area-1",
    language: str = "en",
    channels: tuple[str, ...] = ("sms", "push"),
    opted_out_targets: tuple[str, ...] = (),
) -> NotificationPreference:
    return NotificationPreference.model_validate(
        {
            "user_id": user_id,
            "geo_code": geo_code,
            "language": language,
            "channels": channels,
            "opted_out_targets": opted_out_targets,
        }
    )


def make_template(channel: str = "sms", *, max_length: int = 500) -> AlertTemplate:
    return AlertTemplate.model_validate(
        {
            "template_id": f"tpl-{channel}",
            "version": "tpl-1",
            "channel": channel,
            "body": (
                "{geo_code} {crop_code}: {target_code} risk from {window_from} to "
                "{window_to}. Reason: {reason}. Coverage: {coverage}. "
                "Next: {next_action}. Advisory v{advisory_version}. Issued {issue_time}."
            ),
            "max_length": max_length,
            "approved_by": "approver-1",
            "approved_at": NOW - timedelta(days=1),
        }
    )


def make_template_registry(channels: tuple[str, ...] = ("sms", "whatsapp", "push", "ivr", "web")):
    registry = TemplateRegistry()
    for channel in channels:
        registry.add(make_template(channel))
    return registry


def make_alert_service(
    *,
    advisory_registry: AdvisoryRegistry,
    provider=None,
    clock: Callable[[], datetime] | None = None,
    retry_attempts: int = 1,
    retry_backoff_s: float = 0.0,
    sleep=None,
) -> AlertService:
    return AlertService(
        advisory_registry=advisory_registry,
        template_registry=make_template_registry(),
        provider=provider,
        clock=clock,
        retry_attempts=retry_attempts,
        retry_backoff_s=retry_backoff_s,
        sleep=sleep,
    )


class RecordingProvider:
    def __init__(self) -> None:
        self.sent: list[tuple[RenderedMessage, Recipient]] = []

    def send(self, message: RenderedMessage, recipient: Recipient) -> ProviderReceipt:
        self.sent.append((message, recipient))
        return ProviderReceipt(status="delivered", provider_ref=f"ref-{len(self.sent)}")


class FailingProvider:
    def __init__(self, *, error: str = "provider_down") -> None:
        self.calls = 0
        self.error = error

    def send(self, message: RenderedMessage, recipient: Recipient) -> ProviderReceipt:
        self.calls += 1
        return ProviderReceipt(status="failed", error=self.error)


class FlakyProvider:
    def __init__(self) -> None:
        self.calls = 0

    def send(self, message: RenderedMessage, recipient: Recipient) -> ProviderReceipt:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("transient provider failure")
        return ProviderReceipt(status="delivered", provider_ref="ref-after-retry")


class InspectingProvider:
    """Captures service history from inside the provider call."""

    def __init__(self, service_getter: Callable[[], AlertService]) -> None:
        self._service_getter = service_getter
        self.history_lengths: list[int] = []
        self.delivery_statuses: list[str] = []

    def send(self, message: RenderedMessage, recipient: Recipient) -> ProviderReceipt:
        service = self._service_getter()
        history = service.history()
        self.history_lengths.append(len(history))
        if history:
            self.delivery_statuses.extend(delivery.status for delivery in history[0].deliveries)
        return ProviderReceipt(status="delivered", provider_ref="ref-inspected")

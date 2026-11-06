"""Alert domain model (spec 07 §5–§7).

An alert is generated from a forecast plus an approved advisory. Raw reports
never create an alert. Delivery rows carry the per-recipient status so a
provider failure can never be reported as a successful send.
"""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

RiskBand = Literal["low", "moderate", "high", "urgent", "insufficient"]
TriggerBand = Literal["low", "moderate", "high", "urgent"]

BAND_ORDER: dict[str, int] = {"low": 0, "moderate": 1, "high": 2, "urgent": 3}

Channel = Literal["sms", "whatsapp", "push", "ivr", "web"]
CHANNELS: frozenset[str] = frozenset({"sms", "whatsapp", "push", "ivr", "web"})

DeliveryStatus = Literal["queued", "sent", "delivered", "failed", "suppressed", "opted_out"]
RECEIVED_STATUSES: frozenset[str] = frozenset({"sent", "delivered"})

DriverCode = Literal[
    "rainfall",
    "humidity",
    "temperature",
    "leaf_wetness",
    "verified_reports",
    "seasonal_window",
]


class ForecastSnapshot(BaseModel):
    """The forecast fields the trigger is allowed to read.

    ``drivers`` is a bounded vocabulary, not model prose, so the template can
    never be filled from free text produced by a model.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    forecast_id: str = Field(min_length=1, max_length=120)
    crop_code: str = Field(min_length=1, max_length=80)
    target_code: str = Field(min_length=1, max_length=80)
    geo_code: str = Field(min_length=1, max_length=80)
    band: RiskBand
    coverage: float = Field(ge=0, le=1)
    is_stale: bool
    is_demo: bool
    window_from: AwareDatetime
    window_to: AwareDatetime
    issued_at: AwareDatetime
    drivers: tuple[DriverCode, ...] = ()

    @model_validator(mode="after")
    def _window_order(self) -> ForecastSnapshot:
        if self.window_to <= self.window_from:
            raise ValueError("window_to must be after window_from")
        return self


class AlertPolicy(BaseModel):
    """Approved alert configuration for one area and target."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_id: str = Field(min_length=1, max_length=120)
    geo_code: str = Field(min_length=1, max_length=80)
    target_code: str = Field(min_length=1, max_length=80)
    min_band: TriggerBand
    min_coverage: float = Field(ge=0, le=1)
    cooldowns: dict[str, float]
    channels: tuple[Channel, ...] = Field(min_length=1, max_length=5)
    template_version: str = Field(min_length=1, max_length=80)
    approved_by: str = Field(min_length=1, max_length=120)
    approved_at: AwareDatetime
    active: bool = True

    @model_validator(mode="after")
    def _consistent(self) -> AlertPolicy:
        allowed = set(BAND_ORDER)
        for band, hours in self.cooldowns.items():
            if band not in allowed:
                raise ValueError(f"unknown cooldown band: {band}")
            if hours <= 0:
                raise ValueError("cooldown hours must be positive")
        for band in allowed:
            if band not in self.cooldowns:
                raise ValueError(f"missing cooldown for band: {band}")
        if len(set(self.channels)) != len(self.channels):
            raise ValueError("channels must be unique")
        return self


class NotificationPreference(BaseModel):
    """Per-user channel and target preferences. Changes apply to the next dispatch."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    user_id: str = Field(min_length=1, max_length=120)
    geo_code: str = Field(min_length=1, max_length=80)
    language: str = Field(min_length=2, max_length=16)
    channels: tuple[Channel, ...] = ()
    opted_out_targets: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _unique(self) -> NotificationPreference:
        if len(set(self.channels)) != len(self.channels):
            raise ValueError("channels must be unique")
        if len(set(self.opted_out_targets)) != len(self.opted_out_targets):
            raise ValueError("opted_out_targets must be unique")
        return self


class ProviderReceipt(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    status: Literal["sent", "delivered", "failed"]
    provider_ref: str | None = Field(default=None, max_length=200)
    error: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _failure_has_error(self) -> ProviderReceipt:
        if self.status == "failed" and not self.error:
            raise ValueError("a failed receipt must carry an error")
        return self


class RenderedMessage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    channel: Channel
    template_version: str
    text: str
    updated: bool = False


class AlertDelivery(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    delivery_id: str
    alert_id: str
    user_id: str
    channel: Channel
    status: DeliveryStatus
    provider_ref: str | None = None
    error: str | None = None
    attempt_count: int = Field(default=0, ge=0)
    queued_at: AwareDatetime
    sent_at: AwareDatetime | None = None
    delivered_at: AwareDatetime | None = None
    suppression_reason: str | None = None
    message_version: str | None = None
    message_text: str | None = None
    advisory_id: str | None = None
    advisory_version: int | None = None


class Alert(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    alert_id: str
    forecast_id: str
    geo_code: str
    crop_code: str
    target_code: str
    band: TriggerBand
    coverage: float = Field(ge=0, le=1)
    window_from: AwareDatetime
    window_to: AwareDatetime
    issued_at: AwareDatetime
    generated_at: AwareDatetime
    dedupe_key: str = Field(pattern=r"^[0-9a-f]{64}$")
    updated: bool = False
    suppressed: bool = False
    suppression_reason: str | None = None
    advisory_id: str
    advisory_version: int
    message_version: str
    deliveries: tuple[AlertDelivery, ...] = ()


class AlertFeedback(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    feedback_id: str
    delivery_id: str
    user_id: str
    rating: Literal["useful", "not_useful", "inaccurate"]
    reason: str | None = Field(default=None, max_length=500)
    created_at: AwareDatetime


class InboxItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    alert_id: str
    delivery_id: str
    geo_code: str
    crop_code: str
    target_code: str
    band: TriggerBand
    window_from: AwareDatetime
    window_to: AwareDatetime
    generated_at: AwareDatetime
    channel: Channel
    status: DeliveryStatus
    message_text: str | None
    suppression_reason: str | None


class FeedbackSummary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    counts: dict[str, int]
    total: int

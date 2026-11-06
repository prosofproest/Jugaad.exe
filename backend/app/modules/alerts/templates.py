"""Versioned alert templates and rendering (spec 07 §6, FR-07-08/09/14).

Templates are approved content, not code defaults. Every rendered message is
composed only from structured fields and ends with the fixed sentence that says
this is an early warning, not confirmation. A template that omits a required
field cannot be registered.
"""

from __future__ import annotations

import string
from threading import RLock

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.modules.advisories.models import ActionType, ApprovedAdvisoryView
from app.modules.advisories.validator import find_prohibited_matches
from app.modules.alerts.models import Channel, ForecastSnapshot, RenderedMessage

NOT_CONFIRMATION_SENTENCE = "This is an early warning, not confirmation of disease in your field."

UPDATED_PREFIX = "UPDATED. "

REQUIRED_PLACEHOLDERS: frozenset[str] = frozenset(
    {
        "geo_code",
        "crop_code",
        "target_code",
        "window_from",
        "window_to",
        "reason",
        "next_action",
        "coverage",
        "issue_time",
        "advisory_version",
    }
)

_DRIVER_TEXT: dict[str, str] = {
    "rainfall": "rainfall",
    "humidity": "humidity",
    "temperature": "temperature",
    "leaf_wetness": "leaf wetness",
    "verified_reports": "verified reports",
    "seasonal_window": "seasonal window",
}

_ACTION_TEXT: dict[str, str] = {
    "scout": "inspect plants across the field and record what you see",
    "monitor": "repeat observation over the defined period",
    "sanitise": "remove affected plant material per local practice",
    "crop_management": "follow locally approved crop management practices",
    "escalate": "request expert review or a field visit",
    "record": "keep a photo or record for comparison",
}


class TemplateError(ValueError):
    """A typed template failure carrying a machine-readable code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class AlertTemplate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    template_id: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=80)
    channel: Channel
    body: str = Field(min_length=1, max_length=4000)
    max_length: int = Field(gt=0, le=5000)
    approved_by: str = Field(min_length=1, max_length=120)
    approved_at: AwareDatetime

    @model_validator(mode="after")
    def _placeholders(self) -> AlertTemplate:
        names: set[str] = set()
        for _, field_name, format_spec, conversion in string.Formatter().parse(self.body):
            if field_name is None:
                continue
            if format_spec or conversion:
                raise ValueError("template placeholders must be plain {name} fields")
            if field_name not in REQUIRED_PLACEHOLDERS:
                raise ValueError(f"unknown template placeholder: {field_name}")
            names.add(field_name)
        missing = REQUIRED_PLACEHOLDERS - names
        if missing:
            raise ValueError(f"template is missing placeholders: {sorted(missing)}")
        return self


class TemplateRegistry:
    def __init__(self) -> None:
        self._templates: dict[tuple[str, str], AlertTemplate] = {}
        self._lock = RLock()

    def add(self, template: AlertTemplate) -> None:
        key = (template.channel, template.version)
        with self._lock:
            if key in self._templates:
                raise TemplateError("duplicate_template")
            self._templates[key] = template

    def require(self, channel: str, version: str) -> AlertTemplate:
        with self._lock:
            template = self._templates.get((channel, version))
        if template is None:
            raise TemplateError("template_not_approved")
        return template


def format_reason(drivers: tuple[str, ...]) -> str:
    labels = [_DRIVER_TEXT[driver] for driver in drivers if driver in _DRIVER_TEXT]
    return ", ".join(labels)


def format_actions(action_types: tuple[ActionType, ...]) -> str:
    labels = [_ACTION_TEXT[action] for action in action_types if action in _ACTION_TEXT]
    return "; ".join(labels)


def _context(
    forecast: ForecastSnapshot,
    advisory: ApprovedAdvisoryView,
) -> dict[str, str]:
    return {
        "geo_code": forecast.geo_code,
        "crop_code": forecast.crop_code,
        "target_code": forecast.target_code,
        "window_from": forecast.window_from.date().isoformat(),
        "window_to": forecast.window_to.date().isoformat(),
        "reason": format_reason(forecast.drivers),
        "next_action": format_actions(advisory.action_types),
        "coverage": f"{forecast.coverage:.0%}",
        "issue_time": forecast.issued_at.date().isoformat(),
        "advisory_version": str(advisory.version),
    }


def render_alert(
    *,
    template: AlertTemplate,
    forecast: ForecastSnapshot,
    advisory: ApprovedAdvisoryView,
    updated: bool,
) -> RenderedMessage:
    """Fill a template from structured fields and enforce the channel limit."""

    context = _context(forecast, advisory)
    if not context["reason"]:
        raise TemplateError("missing_reason_codes")
    if not context["next_action"]:
        raise TemplateError("missing_next_action")

    try:
        body = template.body.format_map(context)
    except (KeyError, ValueError) as error:
        raise TemplateError("template_render_failed") from error

    if updated:
        body = UPDATED_PREFIX + body
    text = f"{body} {NOT_CONFIRMATION_SENTENCE}"
    if len(text) > template.max_length:
        raise TemplateError("message_too_long")

    prohibited = find_prohibited_matches("message", text)
    if prohibited:
        raise TemplateError("prohibited_content")

    return RenderedMessage(
        channel=template.channel,
        template_version=template.version,
        text=text,
        updated=updated,
    )

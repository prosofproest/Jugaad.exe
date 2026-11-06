from __future__ import annotations

import pytest
from app.modules.advisories.registry import AdvisoryRegistry
from app.modules.alerts.templates import (
    NOT_CONFIRMATION_SENTENCE,
    AlertTemplate,
    TemplateError,
    TemplateRegistry,
    format_actions,
    format_reason,
    render_alert,
)

from tests.support_notifications import (
    NOW,
    MutableClock,
    make_forecast,
    make_template,
    make_template_registry,
    populate_advisory,
)


def _advisory():
    registry = AdvisoryRegistry(clock=MutableClock())
    populate_advisory(registry)
    return registry.retrieve(
        crop="crop-1", target="target-1", geo="area-1", language="en", now=NOW
    ).items[0]


def _template_data() -> dict:
    return make_template().model_dump()


def test_valid_template_can_be_registered() -> None:
    registry = make_template_registry(channels=("sms",))

    template = registry.require("sms", "tpl-1")

    assert template.channel == "sms"
    assert template.max_length == 500


def test_template_must_declare_every_required_placeholder() -> None:
    data = _template_data()
    data["body"] = data["body"].replace("{coverage}", "")

    with pytest.raises(ValueError, match="missing placeholders"):
        AlertTemplate.model_validate(data)


def test_template_rejects_unknown_placeholders_and_formatting() -> None:
    data = _template_data()
    data["body"] = data["body"] + " {unknown_field}"
    with pytest.raises(ValueError, match="unknown template placeholder"):
        AlertTemplate.model_validate(data)

    data = _template_data()
    data["body"] = data["body"].replace("{geo_code}", "{geo_code!r}")
    with pytest.raises(ValueError, match="plain"):
        AlertTemplate.model_validate(data)


def test_duplicate_and_missing_templates_are_rejected() -> None:
    registry = TemplateRegistry()
    template = make_template()
    registry.add(template)

    with pytest.raises(TemplateError) as caught:
        registry.add(template)
    assert caught.value.code == "duplicate_template"

    with pytest.raises(TemplateError) as caught:
        registry.require("sms", "tpl-999")
    assert caught.value.code == "template_not_approved"


def test_rendered_message_uses_structured_fields_and_the_fixed_sentence() -> None:
    message = render_alert(
        template=make_template(),
        forecast=make_forecast(),
        advisory=_advisory(),
        updated=False,
    )

    assert message.text.endswith(NOT_CONFIRMATION_SENTENCE)
    assert message.updated is False
    assert "area-1" in message.text
    assert "crop-1" in message.text
    assert "target-1" in message.text
    assert "humidity, rainfall" in message.text
    assert "80%" in message.text
    assert "inspect plants across the field" in message.text
    assert "v1" in message.text


def test_updated_message_gets_an_unambiguous_prefix() -> None:
    message = render_alert(
        template=make_template(),
        forecast=make_forecast(),
        advisory=_advisory(),
        updated=True,
    )

    assert message.text.startswith("UPDATED. ")
    assert message.updated is True


def test_missing_reason_codes_and_length_limits_are_enforced() -> None:
    with pytest.raises(TemplateError) as caught:
        render_alert(
            template=make_template(),
            forecast=make_forecast(drivers=()),
            advisory=_advisory(),
            updated=False,
        )
    assert caught.value.code == "missing_reason_codes"

    with pytest.raises(TemplateError) as caught:
        render_alert(
            template=make_template(max_length=20),
            forecast=make_forecast(),
            advisory=_advisory(),
            updated=False,
        )
    assert caught.value.code == "message_too_long"


def test_prohibited_content_in_a_template_is_never_rendered() -> None:
    data = _template_data()
    data["body"] = data["body"] + " Apply fungicide to the field."
    template = AlertTemplate.model_validate(data)

    with pytest.raises(TemplateError) as caught:
        render_alert(
            template=template,
            forecast=make_forecast(),
            advisory=_advisory(),
            updated=False,
        )
    assert caught.value.code == "prohibited_content"


def test_reason_and_action_labels_are_bounded_vocabularies() -> None:
    assert format_reason(("humidity", "leaf_wetness")) == "humidity, leaf wetness"
    assert format_reason(()) == ""
    assert format_actions(("scout", "escalate")) == (
        "inspect plants across the field and record what you see; "
        "request expert review or a field visit"
    )
    assert format_actions(()) == ""

from __future__ import annotations

from datetime import timedelta

import pytest
from app.modules.advisories.registry import AdvisoryRegistry
from app.modules.alerts.trigger import dedupe_key, eligible_recipients, evaluate_trigger

from tests.support_notifications import (
    NOW,
    MutableClock,
    make_draft,
    make_forecast,
    make_policy,
    make_preference,
    populate_advisory,
)


def _published_advisory(registry: AdvisoryRegistry):
    populate_advisory(registry)
    result = registry.retrieve(
        crop="crop-1", target="target-1", geo="area-1", language="en", now=NOW
    )
    assert result.items
    return result.items[0]


def _evaluate(**overrides):
    registry = AdvisoryRegistry(clock=MutableClock())
    advisory = _published_advisory(registry)
    values = {
        "forecast": make_forecast(),
        "policy": make_policy(),
        "advisory": advisory,
        "preferences": (make_preference(),),
        "paused": False,
        "now": NOW,
    }
    values.update(overrides)
    return evaluate_trigger(**values)


def test_high_risk_forecast_triggers_for_opted_in_recipients() -> None:
    result = _evaluate()

    assert result.triggered is True
    assert result.reason == "triggered"
    assert result.recipients == ("user-1",)


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        ({"policy": make_policy(geo_code="area-2")}, "policy_scope_mismatch"),
        ({"policy": make_policy(target_code="target-2")}, "policy_scope_mismatch"),
        ({"forecast": make_forecast(is_demo=True)}, "demo_forecast"),
        ({"paused": True}, "paused"),
        ({"policy": make_policy(active=False)}, "policy_inactive"),
        ({"forecast": make_forecast(is_stale=True)}, "stale_forecast"),
        ({"forecast": make_forecast(band="insufficient")}, "insufficient_band"),
        ({"forecast": make_forecast(band="low")}, "band_below_minimum"),
        ({"forecast": make_forecast(coverage=0.5)}, "low_coverage"),
        ({"forecast": make_forecast(drivers=())}, "missing_reason_codes"),
        ({"advisory": None}, "advisory_unavailable"),
        ({"preferences": ()}, "no_opted_in_recipients"),
    ],
)
def test_every_gate_blocks_the_alert(overrides: dict, expected_reason: str) -> None:
    result = _evaluate(**overrides)

    assert result.triggered is False
    assert result.reason == expected_reason
    assert result.recipients == ()


def test_advisory_scope_mismatch_blocks_the_alert() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    advisory = _published_advisory(registry)

    result = _evaluate(advisory=advisory.model_copy(update={"target_code": "target-2"}))

    assert result.triggered is False
    assert result.reason == "advisory_scope_mismatch"


def test_expired_advisory_blocks_the_alert() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    advisory = _published_advisory(registry)

    result = _evaluate(advisory=advisory, now=NOW + timedelta(days=60))

    assert result.triggered is False
    assert result.reason == "advisory_expired"


def test_cross_area_advisory_blocks_the_alert() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    populate_advisory(registry, draft=make_draft(geo_scope=["area-2"]))
    advisory = registry.retrieve(
        crop="crop-1", target="target-1", geo="area-2", language="en", now=NOW
    ).items[0]

    result = _evaluate(advisory=advisory)

    assert result.triggered is False
    assert result.reason == "advisory_scope_mismatch"


def test_all_supported_areas_advisory_matches_the_forecast_area() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    populate_advisory(registry, draft=make_draft(geo_scope=["all_supported_areas"]))
    advisory = registry.retrieve(
        crop="crop-1", target="target-1", geo="area-1", language="en", now=NOW
    ).items[0]

    result = _evaluate(advisory=advisory)

    assert result.triggered is True


def test_dedupe_key_is_deterministic_and_band_sensitive() -> None:
    first = dedupe_key(
        geo_code="area-1",
        target_code="target-1",
        band="high",
        window_from=NOW,
        window_to=NOW + timedelta(days=7),
    )
    same = dedupe_key(
        geo_code="area-1",
        target_code="target-1",
        band="high",
        window_from=NOW,
        window_to=NOW + timedelta(days=7),
    )
    escalated = dedupe_key(
        geo_code="area-1",
        target_code="target-1",
        band="urgent",
        window_from=NOW,
        window_to=NOW + timedelta(days=7),
    )

    assert first == same
    assert first != escalated
    assert len(first) == 64


def test_recipient_selection_filters_scope_language_channel_and_opt_out() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    advisory = _published_advisory(registry)
    preferences = (
        make_preference(user_id="a"),
        make_preference(user_id="b", geo_code="area-2"),
        make_preference(user_id="c", language="kn"),
        make_preference(user_id="d", channels=("whatsapp",)),
        make_preference(user_id="e", opted_out_targets=("target-1",)),
        make_preference(user_id="f", channels=("sms",)),
    )

    recipients = eligible_recipients(
        forecast=make_forecast(),
        policy=make_policy(),
        advisory=advisory,
        preferences=preferences,
    )

    assert recipients == ("a", "f")

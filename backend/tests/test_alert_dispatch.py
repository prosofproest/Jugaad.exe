from __future__ import annotations

from datetime import timedelta

import pytest
from app.modules.advisories.registry import AdvisoryRegistry
from app.modules.alerts.dispatch import FeedbackError
from app.modules.alerts.templates import NOT_CONFIRMATION_SENTENCE

from tests.support_notifications import (
    NOW,
    FailingProvider,
    FlakyProvider,
    InspectingProvider,
    MutableClock,
    RecordingProvider,
    make_alert_service,
    make_forecast,
    make_policy,
    make_preference,
    populate_advisory,
)


def _service(
    *,
    provider=None,
    clock: MutableClock | None = None,
    retry_attempts: int = 1,
    retry_backoff_s: float = 0.0,
    sleep=None,
):
    clock = clock or MutableClock()
    advisories = AdvisoryRegistry(clock=clock)
    populate_advisory(advisories)
    service = make_alert_service(
        advisory_registry=advisories,
        provider=provider,
        clock=clock,
        retry_attempts=retry_attempts,
        retry_backoff_s=retry_backoff_s,
        sleep=sleep,
    )
    return service, clock


def _two_users(service) -> None:
    service.set_preference(make_preference(user_id="user-1"))
    service.set_preference(make_preference(user_id="user-2", channels=("sms",)))


def test_high_risk_generates_exactly_one_alert_with_recorded_delivery() -> None:
    provider = RecordingProvider()
    service, _ = _service(provider=provider)
    _two_users(service)

    result = service.dispatch(forecast=make_forecast(), policy=make_policy(), language="en")

    assert result.triggered is True
    assert result.reason == "triggered"
    assert result.deduplicated is False
    assert result.recipients == ("user-1", "user-2")

    alerts = service.history()
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_id == result.alert.alert_id  # type: ignore[union-attr]
    assert {delivery.user_id for delivery in alert.deliveries} == {"user-1", "user-2"}
    assert all(delivery.status == "delivered" for delivery in alert.deliveries)
    assert all(delivery.provider_ref for delivery in alert.deliveries)
    assert all(delivery.sent_at == NOW for delivery in alert.deliveries)
    assert all(delivery.delivered_at == NOW for delivery in alert.deliveries)
    assert all(
        delivery.message_text.endswith(NOT_CONFIRMATION_SENTENCE)
        for delivery in alert.deliveries
    )
    assert len(provider.sent) == 3
    assert service.get_alert(alert.alert_id) is not None


def test_replaying_the_same_forecast_creates_no_duplicate() -> None:
    provider = RecordingProvider()
    service, _ = _service(provider=provider)
    _two_users(service)
    forecast = make_forecast()
    policy = make_policy()

    first = service.dispatch(forecast=forecast, policy=policy, language="en")
    second = service.dispatch(forecast=forecast, policy=policy, language="en")

    assert second.reason == "duplicate"
    assert second.deduplicated is True
    assert second.alert.alert_id == first.alert.alert_id  # type: ignore[union-attr]
    assert len(service.history()) == 1
    assert len(provider.sent) == 3


def test_missing_provider_is_recorded_as_a_failure_not_a_send() -> None:
    service, _ = _service(provider=None)
    _two_users(service)

    result = service.dispatch(forecast=make_forecast(), policy=make_policy(), language="en")

    assert result.triggered is True
    assert result.reason == "delivery_failed"
    alert = service.history()[0]
    assert all(delivery.status == "failed" for delivery in alert.deliveries)
    assert all(delivery.error == "provider_not_configured" for delivery in alert.deliveries)
    assert all(delivery.sent_at is None for delivery in alert.deliveries)
    assert service.inbox("user-1") == []


def test_downgrade_does_not_generate_a_new_alert() -> None:
    provider = RecordingProvider()
    service, _ = _service(provider=provider)
    _two_users(service)
    policy = make_policy()
    urgent = make_forecast(band="urgent")
    high = make_forecast(band="high")

    service.dispatch(forecast=urgent, policy=policy, language="en")
    result = service.dispatch(forecast=high, policy=policy, language="en")

    assert result.triggered is False
    assert result.reason == "downgrade"
    assert len(service.history()) == 1
    assert any(
        event.event_type == "alert.downgrade_suppressed" for event in service.audit_events()
    )


def test_escalation_generates_a_new_marked_updated_alert() -> None:
    provider = RecordingProvider()
    service, _ = _service(provider=provider)
    _two_users(service)
    policy = make_policy()

    service.dispatch(forecast=make_forecast(band="high"), policy=policy, language="en")
    result = service.dispatch(
        forecast=make_forecast(band="urgent"), policy=policy, language="en"
    )

    assert result.triggered is True
    assert result.alert.updated is True  # type: ignore[union-attr]
    assert all(
        delivery.message_text.startswith("UPDATED. ")
        for delivery in result.alert.deliveries  # type: ignore[union-attr]
    )
    assert len(service.history()) == 2


def test_cooldown_suppresses_repeats_but_allows_after_expiry() -> None:
    provider = RecordingProvider()
    service, clock = _service(provider=provider)
    _two_users(service)
    policy = make_policy()
    first = make_forecast(window_to=NOW)

    service.dispatch(forecast=first, policy=policy, language="en")
    assert len(provider.sent) == 3

    clock.advance(hours=1)
    early_repeat = make_forecast(
        window_from=NOW + _days(14), window_to=NOW + _days(21)
    )
    suppressed = service.dispatch(
        forecast=early_repeat, policy=policy, language="en"
    )

    assert suppressed.reason == "suppressed"
    assert suppressed.alert.suppressed is True  # type: ignore[union-attr]
    assert all(
        delivery.status == "suppressed"
        for delivery in suppressed.alert.deliveries  # type: ignore[union-attr]
    )
    assert len(provider.sent) == 3

    clock.advance(hours=25)
    late_repeat = make_forecast(
        window_from=NOW + _days(28), window_to=NOW + _days(35)
    )
    delivered = service.dispatch(forecast=late_repeat, policy=policy, language="en")

    assert delivered.reason == "triggered"
    assert len(provider.sent) == 6


def test_no_opted_in_recipient_does_not_create_an_alert() -> None:
    service, _ = _service(provider=RecordingProvider())

    result = service.dispatch(forecast=make_forecast(), policy=make_policy(), language="en")

    assert result.triggered is False
    assert result.reason == "no_opted_in_recipients"
    assert service.history() == []


def test_pause_stops_dispatch_until_resumed() -> None:
    provider = RecordingProvider()
    service, _ = _service(provider=provider)
    _two_users(service)
    policy = make_policy()

    with pytest.raises(ValueError):
        service.pause(geo_code="area-1", target_code="target-1", actor_id="ops-1", reason=" ")

    service.pause(
        geo_code="area-1", target_code="target-1", actor_id="ops-1", reason="synthetic review"
    )
    assert service.is_paused("area-1", "target-1")
    paused = service.dispatch(forecast=make_forecast(), policy=policy, language="en")
    assert paused.reason == "paused"
    assert service.history() == []

    service.resume(geo_code="area-1", target_code="target-1", actor_id="ops-1")
    assert not service.is_paused("area-1", "target-1")
    resumed = service.dispatch(forecast=make_forecast(), policy=policy, language="en")
    assert resumed.reason == "triggered"


def test_failed_provider_is_retried_and_never_marked_sent() -> None:
    provider = FailingProvider(error="provider_down")
    service, _ = _service(provider=provider, retry_attempts=2)
    service.set_preference(make_preference(user_id="user-1", channels=("sms",)))

    result = service.dispatch(forecast=make_forecast(), policy=make_policy(), language="en")

    assert provider.calls == 2
    assert result.reason == "delivery_failed"
    delivery = service.history()[0].deliveries[0]
    assert delivery.status == "failed"
    assert delivery.error == "provider_down"
    assert delivery.attempt_count == 2
    assert delivery.sent_at is None
    assert service.inbox("user-1") == []


def test_retry_backoff_delays_between_attempts() -> None:
    sleeps: list[float] = []
    provider = FailingProvider(error="provider_down")
    service, _ = _service(
        provider=provider,
        retry_attempts=3,
        retry_backoff_s=0.5,
        sleep=sleeps.append,
    )
    service.set_preference(make_preference(user_id="user-1", channels=("sms",)))

    service.dispatch(forecast=make_forecast(), policy=make_policy(), language="en")

    assert provider.calls == 3
    assert sleeps == [0.5, 1.0]


def test_transient_provider_failure_recovers_on_retry() -> None:
    provider = FlakyProvider()
    service, _ = _service(provider=provider, retry_attempts=2)
    service.set_preference(make_preference(user_id="user-1", channels=("sms",)))

    result = service.dispatch(forecast=make_forecast(), policy=make_policy(), language="en")

    assert provider.calls == 2
    assert result.reason == "triggered"
    delivery = service.history()[0].deliveries[0]
    assert delivery.status == "delivered"
    assert delivery.provider_ref == "ref-after-retry"
    assert delivery.attempt_count == 2


def test_alert_is_persisted_before_the_provider_is_called() -> None:
    holder: dict = {}
    provider = InspectingProvider(lambda: holder["service"])
    service, _ = _service(provider=provider)
    holder["service"] = service
    service.set_preference(make_preference(user_id="user-1", channels=("sms",)))

    service.dispatch(forecast=make_forecast(), policy=make_policy(), language="en")

    assert provider.history_lengths == [1]
    assert provider.delivery_statuses == ["queued"]


def test_inbox_only_lists_delivered_items_and_paginates() -> None:
    service, _ = _service(provider=RecordingProvider())
    _two_users(service)

    service.dispatch(forecast=make_forecast(), policy=make_policy(), language="en")

    items = service.inbox("user-1")
    assert len(items) == 2
    assert {item.channel for item in items} == {"sms", "push"}
    assert all(item.status == "delivered" for item in items)
    assert service.inbox("user-2") != []
    assert service.inbox("unknown-user") == []

    first_page = service.inbox("user-1", limit=1)
    second_page = service.inbox("user-1", limit=1, cursor="1")
    assert len(first_page) == 1
    assert len(second_page) == 1
    assert first_page[0].delivery_id != second_page[0].delivery_id

    with pytest.raises(ValueError):
        service.inbox("user-1", limit=0)
    with pytest.raises(ValueError):
        service.inbox("user-1", cursor="not-a-number")


def test_feedback_is_owner_scoped_and_summarised() -> None:
    service, _ = _service(provider=RecordingProvider())
    _two_users(service)
    result = service.dispatch(forecast=make_forecast(), policy=make_policy(), language="en")
    delivery = result.alert.deliveries[0]  # type: ignore[union-attr]

    feedback = service.submit_feedback(
        delivery_id=delivery.delivery_id, user_id=delivery.user_id, rating="useful"
    )
    assert feedback.rating == "useful"

    with pytest.raises(FeedbackError) as caught:
        service.submit_feedback(
            delivery_id=delivery.delivery_id, user_id="someone-else", rating="useful"
        )
    assert caught.value.code == "not_owner"

    with pytest.raises(FeedbackError) as caught:
        service.submit_feedback(
            delivery_id=delivery.delivery_id, user_id=delivery.user_id, rating="great"
        )
    assert caught.value.code == "invalid_rating"

    with pytest.raises(FeedbackError) as caught:
        service.submit_feedback(
            delivery_id="del_missing", user_id=delivery.user_id, rating="useful"
        )
    assert caught.value.code == "delivery_not_found"

    summary = service.feedback_summary()
    assert summary.counts == {"useful": 1, "not_useful": 0, "inaccurate": 0}
    assert summary.total == 1
    assert service.feedback_summary(band="urgent").total == 0


def test_suppressed_delivery_cannot_receive_feedback() -> None:
    service, clock = _service(provider=RecordingProvider())
    _two_users(service)
    policy = make_policy()
    service.dispatch(
        forecast=make_forecast(window_to=NOW), policy=policy, language="en"
    )
    clock.advance(hours=1)
    suppressed = service.dispatch(
        forecast=make_forecast(window_from=NOW + _days(14), window_to=NOW + _days(21)),
        policy=policy,
        language="en",
    )
    delivery = suppressed.alert.deliveries[0]  # type: ignore[union-attr]

    with pytest.raises(FeedbackError) as caught:
        service.submit_feedback(
            delivery_id=delivery.delivery_id, user_id=delivery.user_id, rating="useful"
        )
    assert caught.value.code == "delivery_not_received"


def test_dispatch_and_delivery_events_are_audited() -> None:
    service, _ = _service(provider=RecordingProvider())
    _two_users(service)

    service.dispatch(forecast=make_forecast(), policy=make_policy(), language="en")

    event_types = [event.event_type for event in service.audit_events()]
    assert "alert.preference_updated" in event_types
    assert "alert.generated" in event_types
    assert "alert.delivery_sent" in event_types


def _days(value: int) -> timedelta:
    return timedelta(days=value)

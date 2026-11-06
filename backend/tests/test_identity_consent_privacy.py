"""Consent versioning, privacy requests, deletion and retention (spec 03 §5–§7)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from app.core.errors import ApiError
from app.modules.identity.models import (
    ConsentDecision,
    ConsentUpdate,
    PrivacyRequestCreate,
)
from app.modules.identity.service import (
    CONSENT_CATALOG_VERSION,
    IdentityService,
    default_consent_catalog,
)

from tests.support_identity import (
    FARMER_PHONE,
    SECRET,
    admin_context,
    bootstrap_admin,
    farmer_context,
    farmer_tokens,
    make_identity_service,
)


def _accept_required(service: IdentityService, context, *, research: bool = False) -> None:
    overview = service.consent_overview(context.user.user_id)
    decisions = [
        ConsentDecision(consent_type=state.consent_type, granted=True)
        for state in overview.states
        if state.required
    ]
    decisions.append(ConsentDecision(consent_type="research_model_improvement", granted=research))
    service.update_consents(context, ConsentUpdate(decisions=decisions, channel="api-test"))


def test_consent_catalog_is_versioned_plain_language_and_not_legally_final() -> None:
    catalog = default_consent_catalog()

    assert {item.consent_type for item in catalog} == {
        "service_privacy",
        "image_assessment",
        "approximate_location",
        "research_model_improvement",
        "extension_worker_contact",
    }
    assert all(item.version == CONSENT_CATALOG_VERSION for item in catalog)
    assert all(item.text_hash for item in catalog)
    assert all(item.summary for item in catalog)
    assert all(
        "draft" in item.summary.lower()
        for item in catalog
        if item.consent_type == "service_privacy"
    )
    required = {item.consent_type for item in catalog if item.required}
    assert required == {"service_privacy", "image_assessment", "approximate_location"}
    assert all("pesticide" not in item.summary.lower() for item in catalog)


def test_required_consent_is_missing_until_explicitly_recorded() -> None:
    service, sender, _ = make_identity_service()
    context = farmer_context(service, sender)

    overview = service.consent_overview(context.user.user_id)

    assert overview.consent_complete is False
    assert set(overview.missing_required) == {
        "service_privacy",
        "image_assessment",
        "approximate_location",
    }
    with pytest.raises(ApiError) as error:
        service.assert_required_consents(context.user.user_id)
    assert error.value.code == "consent_required"


def test_consent_record_captures_version_timestamp_channel_and_text_hash() -> None:
    service, sender, clock = make_identity_service()
    context = farmer_context(service, sender)

    _accept_required(service, context)
    records = service.store.consents_for_user(context.user.user_id)

    assert len(records) == 4
    assert all(record.version == CONSENT_CATALOG_VERSION for record in records)
    assert all(record.recorded_at == clock.now for record in records)
    assert all(record.channel == "api-test" for record in records)
    assert all(record.text_hash for record in records)
    assert service.consent_overview(context.user.user_id).consent_complete is True


def test_optional_research_consent_can_be_withdrawn_without_blocking() -> None:
    service, sender, _ = make_identity_service()
    context = farmer_context(service, sender)
    _accept_required(service, context, research=True)

    overview = service.consent_overview(context.user.user_id)
    research = next(
        state for state in overview.states if state.consent_type == "research_model_improvement"
    )
    assert research.granted is True

    updated = service.update_consents(
        context,
        ConsentUpdate(
            decisions=[ConsentDecision(consent_type="research_model_improvement", granted=False)],
            channel="api-test",
        ),
    )

    assert updated.consent_complete is True
    research = next(
        state for state in updated.states if state.consent_type == "research_model_improvement"
    )
    assert research.granted is False
    service.assert_required_consents(context.user.user_id)


def test_duplicate_consent_decision_is_rejected() -> None:
    service, sender, _ = make_identity_service()
    context = farmer_context(service, sender)

    with pytest.raises(ApiError) as error:
        service.update_consents(
            context,
            ConsentUpdate(
                decisions=[
                    ConsentDecision(consent_type="service_privacy", granted=True),
                    ConsentDecision(consent_type="service_privacy", granted=False),
                ]
            ),
        )
    assert error.value.code == "duplicate_consent"


def test_consent_version_change_requires_reconsent() -> None:
    service, sender, clock = make_identity_service()
    context = farmer_context(service, sender)
    _accept_required(service, context)
    assert service.consent_overview(context.user.user_id).consent_complete is True

    new_version = "draft-2026-11-07"
    new_catalog = [
        item.model_copy(update={"version": new_version, "text_hash": f"hash-{item.consent_type}"})
        for item in default_consent_catalog()
    ]
    updated_service = IdentityService(
        secret=SECRET,
        store=service.store,
        clock=clock,
        consent_catalog=new_catalog,
    )

    overview = updated_service.consent_overview(context.user.user_id)

    assert overview.consent_complete is False
    assert all(
        state.needs_reconsent
        for state in overview.states
        if state.consent_type in overview.missing_required
    )
    with pytest.raises(ApiError) as error:
        updated_service.assert_required_consents(context.user.user_id)
    assert error.value.code == "consent_required"


def test_export_requires_a_written_purpose_and_audits_both_events() -> None:
    service, sender, _ = make_identity_service()
    context = farmer_context(service, sender)

    with pytest.raises(ApiError) as missing:
        service.export_user_data(context, purpose="short")
    assert missing.value.code == "purpose_required"

    bundle = service.export_user_data(context, purpose="synthetic account access request")

    assert bundle.user.user_id == context.user.user_id
    assert bundle.user.phone == FARMER_PHONE
    event_types = [event.event_type for event in service.audit_events()]
    assert "privacy.export_requested" in event_types
    assert "export.generated" in event_types
    serialised = bundle.model_dump_json()
    assert "password_hash" not in serialised
    assert "mfa_secret" not in serialised


def test_export_contains_only_the_callers_records() -> None:
    service, sender, clock = make_identity_service()
    bootstrap_admin(service)
    admin_context(service, clock)
    first = farmer_context(service, sender)
    second = farmer_context(service, sender, phone="+10000000002")

    bundle = service.export_user_data(first, purpose="synthetic self access export")

    assert all(event.get("actor_id") != second.user.user_id for event in bundle.audit_events)
    assert all(event.get("entity_id") != second.user.user_id for event in bundle.audit_events)


def test_privacy_request_is_recorded_and_listed_for_the_owner() -> None:
    service, sender, _ = make_identity_service()
    context = farmer_context(service, sender)

    request = service.record_privacy_request(
        context,
        PrivacyRequestCreate(
            kind="objection",
            detail="Synthetic objection request for test coverage.",
            reason="synthetic privacy test",
        ),
    )

    assert request.status == "queued"
    assert request.kind == "objection"
    assert service.list_privacy_requests(context) == [request]
    assert any(event.event_type == "privacy.request_recorded" for event in service.audit_events())


def test_deletion_requires_confirmation_and_queued_reports_to_be_resolved() -> None:
    queued = {"count": 2}
    service, sender, _ = make_identity_service()
    context = farmer_context(service, sender)
    service._queued_report_count = lambda _user_id: queued["count"]

    with pytest.raises(ApiError) as confirmation:
        service.delete_account(context, confirmation="delete", reason="synthetic deletion")
    assert confirmation.value.code == "deletion_confirmation_required"

    with pytest.raises(ApiError) as pending:
        service.delete_account(context, confirmation="DELETE", reason="synthetic deletion")
    assert pending.value.code == "queued_reports_exist"

    queued["count"] = 0
    result = service.delete_account(context, confirmation="DELETE", reason="synthetic deletion")

    assert result.status == "scheduled"
    assert result.hard_delete_after is None
    assert service.store.get_user(context.user.user_id).status == "deleted"  # type: ignore[union-attr]


def test_deletion_revokes_sessions_and_only_schedules_hard_delete_when_policy_exists() -> None:
    service, sender, _ = make_identity_service()
    tokens = farmer_tokens(service, sender)
    context = service.resolve_access_token(tokens.access_token)

    service.delete_account(context, confirmation="DELETE", reason="synthetic deletion")

    with pytest.raises(ApiError) as access:
        service.resolve_access_token(tokens.access_token)
    assert access.value.code == "token_invalid"
    with pytest.raises(ApiError) as refresh:
        service.refresh(tokens.refresh_token)
    assert refresh.value.code == "token_invalid"
    event = service.audit_events()[-1]
    assert event.event_type == "privacy.deleted"
    assert event.detail["hard_delete_scheduled"] == "False"

    policy_service, policy_sender, _ = make_identity_service()
    policy_tokens = farmer_tokens(policy_service, policy_sender)
    policy_context = policy_service.resolve_access_token(policy_tokens.access_token)
    policy_service._deletion_retention = timedelta(days=30)

    result = policy_service.delete_account(
        policy_context, confirmation="DELETE", reason="synthetic deletion with policy"
    )
    assert result.hard_delete_after is not None
    assert result.hard_delete_after > result.deleted_at


def test_retention_job_purges_only_short_lived_credentials_and_records_a_reason() -> None:
    service, sender, clock = make_identity_service()
    bootstrap_admin(service)
    admin = admin_context(service, clock)
    service.request_otp(FARMER_PHONE)
    farmer_tokens(service, sender)
    service.request_otp("+10000000002")
    clock.advance(days=31)

    result = service.run_retention(admin, "synthetic scheduled retention run")

    assert result.expired_otp_challenges >= 1
    assert result.expired_refresh_tokens >= 1
    assert result.expired_mfa_challenges == 0
    assert service.store.get_otp(FARMER_PHONE) is None
    event = service.audit_events()[-1]
    assert event.event_type == "maintenance.retention_run"
    assert event.detail["reason"] == "synthetic scheduled retention run"
    assert "D10" in result.note


def test_retention_job_requires_an_admin_and_a_reason() -> None:
    service, sender, clock = make_identity_service()
    bootstrap_admin(service)
    farmer = farmer_context(service, sender)

    with pytest.raises(ApiError) as forbidden:
        service.run_retention(farmer, "synthetic retention attempt")
    assert forbidden.value.code == "forbidden"

    admin = admin_context(service, clock)
    with pytest.raises(ApiError) as reason:
        service.run_retention(admin, "short")
    assert reason.value.code == "reason_required"

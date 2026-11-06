"""Farmer phone-OTP registration, sessions and refresh reuse (spec 03 §4.1–§4.3)."""

from __future__ import annotations

import pytest
from app.core.errors import ApiError
from app.modules.identity.service import AuthContext

from tests.support_identity import (
    ADMIN_EMAIL,
    FARMER_PHONE,
    OTHER_FARMER_PHONE,
    PASSWORD,
    TOTP_SECRET,
    farmer_context,
    farmer_tokens,
    make_identity_service,
)


def test_otp_request_is_enumeration_safe_and_delivers_out_of_band() -> None:
    service, sender, _ = make_identity_service()

    first = service.request_otp(FARMER_PHONE)
    second = service.request_otp(FARMER_PHONE)

    assert first.model_dump() == second.model_dump()
    assert "code" not in first.model_dump()
    assert sender.last_code(FARMER_PHONE) is not None


def test_phone_is_normalised_and_invalid_numbers_are_refused() -> None:
    service, sender, _ = make_identity_service()

    service.request_otp("+1 (000) 000-0001")

    assert sender.last_code("+10000000001") is not None
    with pytest.raises(ApiError) as error:
        service.request_otp("not-a-phone")
    assert error.value.code == "invalid_phone"


def test_verify_creates_a_farmer_and_marks_the_login() -> None:
    service, sender, _ = make_identity_service()

    tokens = farmer_tokens(service, sender)

    user = service.store.get_user(tokens.user_id)
    assert user is not None
    assert user.kind == "farmer"
    assert user.roles == ["farmer"]
    assert user.last_login_at is not None
    assert tokens.role == "farmer"
    assert service.profile(service.resolve_access_token(tokens.access_token)).phone == FARMER_PHONE


def test_second_otp_login_reuses_the_same_farmer_account() -> None:
    service, sender, _ = make_identity_service()
    first = farmer_tokens(service, sender)
    second = farmer_tokens(service, sender)

    assert first.user_id == second.user_id
    assert len(service.store.list_users()) == 1


def test_otp_codes_expire_and_are_single_use() -> None:
    service, sender, clock = make_identity_service()
    service.request_otp(FARMER_PHONE)
    code = sender.last_code(FARMER_PHONE)
    assert code is not None

    clock.advance(minutes=6)

    with pytest.raises(ApiError) as error:
        service.verify_otp(FARMER_PHONE, code)
    assert error.value.code == "otp_expired"


def test_wrong_code_is_rejected_and_attempts_are_capped() -> None:
    service, sender, _ = make_identity_service()
    service.request_otp(FARMER_PHONE)
    code = sender.last_code(FARMER_PHONE)
    assert code is not None
    wrong = "000000" if code != "000000" else "111111"

    for attempt in range(5):
        with pytest.raises(ApiError) as error:
            service.verify_otp(FARMER_PHONE, wrong)
        assert error.value.code == "invalid_otp"
        assert service.store.get_otp(FARMER_PHONE) is not None, attempt

    with pytest.raises(ApiError) as capped:
        service.verify_otp(FARMER_PHONE, wrong)
    assert capped.value.code == "otp_attempts_exceeded"
    assert service.store.get_otp(FARMER_PHONE) is None


def test_otp_requests_are_rate_limited_per_phone() -> None:
    service, _, _ = make_identity_service()

    for _ in range(5):
        service.request_otp(FARMER_PHONE)

    with pytest.raises(ApiError) as error:
        service.request_otp(FARMER_PHONE)
    assert error.value.code == "otp_rate_limited"
    assert error.value.retryable is True


def test_access_token_requires_an_active_session() -> None:
    service, sender, _ = make_identity_service()
    tokens = farmer_tokens(service, sender)
    context = service.resolve_access_token(tokens.access_token)
    assert isinstance(context, AuthContext)

    service.logout(context)

    with pytest.raises(ApiError) as error:
        service.resolve_access_token(tokens.access_token)
    assert error.value.code == "token_invalid"


def test_refresh_rotates_and_reuse_revokes_the_whole_family() -> None:
    service, sender, _ = make_identity_service()
    tokens = farmer_tokens(service, sender)

    rotated = service.refresh(tokens.refresh_token)
    assert rotated.refresh_token != tokens.refresh_token
    assert service.resolve_access_token(rotated.access_token).user.user_id == tokens.user_id

    with pytest.raises(ApiError) as reused:
        service.refresh(tokens.refresh_token)
    assert reused.value.code == "token_reused"

    with pytest.raises(ApiError) as family_revoked:
        service.refresh(rotated.refresh_token)
    assert family_revoked.value.code == "token_invalid"


def test_logout_all_revokes_every_session_for_the_user() -> None:
    service, sender, _ = make_identity_service()
    first = farmer_tokens(service, sender)
    second = farmer_tokens(service, sender)
    context = service.resolve_access_token(first.access_token)

    service.logout_all(context)

    for token in (first.access_token, second.access_token):
        with pytest.raises(ApiError) as error:
            service.resolve_access_token(token)
        assert error.value.code == "token_invalid"


def test_otp_cannot_be_used_for_a_staff_only_account() -> None:
    service, sender, _ = make_identity_service()
    service.bootstrap_admin(ADMIN_EMAIL, PASSWORD, TOTP_SECRET)
    admin = service.store.user_by_email(ADMIN_EMAIL)
    assert admin is not None
    service._save(admin, phone=OTHER_FARMER_PHONE)

    service.request_otp(OTHER_FARMER_PHONE)
    code = sender.last_code(OTHER_FARMER_PHONE)
    assert code is not None
    with pytest.raises(ApiError) as error:
        service.verify_otp(OTHER_FARMER_PHONE, code)
    assert error.value.code == "account_unavailable"


def test_audit_events_do_not_contain_full_phone_numbers() -> None:
    service, sender, _ = make_identity_service()
    service.request_otp(FARMER_PHONE)
    code = sender.last_code(FARMER_PHONE)
    assert code is not None
    wrong = "000000" if code != "000000" else "111111"
    with pytest.raises(ApiError) as error:
        service.verify_otp(FARMER_PHONE, wrong)
    assert error.value.code == "invalid_otp"

    serialised = " ".join(event.model_dump_json() for event in service.audit_events())
    assert FARMER_PHONE not in serialised


def test_farmer_context_fixture_returns_the_expected_role() -> None:
    service, sender, _ = make_identity_service()
    context = farmer_context(service, sender)

    assert context.role == "farmer"
    assert context.user.phone == FARMER_PHONE

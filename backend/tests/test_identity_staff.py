"""Staff provisioning, password+MFA login, roles and admin audit (spec 03 §2–§4)."""

from __future__ import annotations

import pytest
from app.core.errors import ApiError
from app.modules.identity.models import (
    AdminExportRequest,
    LoginRequest,
    RoleUpdateRequest,
    StaffCreateRequest,
    UserStatusUpdate,
)
from app.modules.identity.security import totp_code
from app.modules.identity.service import AuthContext
from pydantic import SecretStr

from tests.support_identity import (
    ADMIN_EMAIL,
    FARMER_PHONE,
    PASSWORD,
    STAFF_EMAIL,
    TOTP_SECRET,
    admin_context,
    bootstrap_admin,
    farmer_context,
    login,
    make_identity_service,
    provision_staff,
)


def test_bootstrap_admin_hashes_the_password_and_enables_mfa() -> None:
    service, _, _ = make_identity_service()

    user = service.bootstrap_admin(ADMIN_EMAIL, PASSWORD, TOTP_SECRET)

    assert user is not None
    assert user.roles == ["admin"]
    assert user.password_hash is not None
    assert PASSWORD not in user.password_hash
    assert user.mfa_enabled is True
    assert service.bootstrap_admin(ADMIN_EMAIL, PASSWORD, TOTP_SECRET) is None


def test_bootstrap_rejects_a_short_password() -> None:
    service, _, _ = make_identity_service()

    with pytest.raises(ApiError) as error:
        service.bootstrap_admin(ADMIN_EMAIL, "short", TOTP_SECRET)
    assert error.value.code == "weak_password"


def test_admin_login_requires_mfa_before_issuing_tokens() -> None:
    service, _, clock = make_identity_service()
    bootstrap_admin(service)

    response = service.login_staff(LoginRequest(email=ADMIN_EMAIL, password=SecretStr(PASSWORD)))

    assert response.mfa_required is True
    assert response.tokens is None
    assert response.challenge_token is not None

    tokens = service.verify_mfa(response.challenge_token, totp_code(TOTP_SECRET, clock.now))

    assert tokens.role == "admin"
    assert service.resolve_access_token(tokens.access_token).role == "admin"


def test_wrong_totp_is_rejected_and_audited() -> None:
    service, _, clock = make_identity_service()
    bootstrap_admin(service)
    response = service.login_staff(LoginRequest(email=ADMIN_EMAIL, password=SecretStr(PASSWORD)))
    assert response.challenge_token is not None
    real = totp_code(TOTP_SECRET, clock.now)
    wrong = "000000" if real != "000000" else "111111"

    with pytest.raises(ApiError) as error:
        service.verify_mfa(response.challenge_token, wrong)
    assert error.value.code == "invalid_credentials"
    assert any(event.event_type == "auth.login_failed" for event in service.audit_events())


def test_staff_lockout_after_ten_failures_and_unlock_by_time() -> None:
    service, _, clock = make_identity_service()
    bootstrap_admin(service)

    for _ in range(10):
        with pytest.raises(ApiError):
            service.login_staff(
                LoginRequest(email=ADMIN_EMAIL, password=SecretStr("wrong password entirely"))
            )

    with pytest.raises(ApiError) as locked:
        service.login_staff(LoginRequest(email=ADMIN_EMAIL, password=SecretStr(PASSWORD)))
    assert locked.value.code == "account_locked"

    clock.advance(minutes=16)
    tokens = login(service, clock)
    assert tokens.role == "admin"


def test_extension_worker_mfa_is_optional_but_required_roles_always_get_it() -> None:
    service, _, clock = make_identity_service()
    bootstrap_admin(service)
    admin = admin_context(service, clock)

    worker = provision_staff(service, clock, admin, roles=["extension_worker"], require_mfa=False)
    pathologist = provision_staff(
        service,
        clock,
        admin,
        email="pathologist@example.test",
        roles=["pathologist"],
        require_mfa=False,
    )

    assert worker.mfa_secret is None
    assert pathologist.mfa_secret is not None

    worker_response = service.login_staff(
        LoginRequest(email=STAFF_EMAIL, password=SecretStr(PASSWORD))
    )
    assert worker_response.mfa_required is False
    assert worker_response.tokens is not None

    pathologist_response = service.login_staff(
        LoginRequest(email="pathologist@example.test", password=SecretStr(PASSWORD))
    )
    assert pathologist_response.mfa_required is True


def test_staff_provisioning_rejects_farmer_roles_weak_passwords_and_duplicates() -> None:
    service, _, clock = make_identity_service()
    bootstrap_admin(service)
    admin = admin_context(service, clock)

    with pytest.raises(ApiError) as farmer_role:
        provision_staff(service, clock, admin, roles=["farmer"])
    assert farmer_role.value.code == "invalid_role"

    with pytest.raises(ApiError) as weak:
        service.provision_staff(
            admin,
            StaffCreateRequest(
                email="weak@example.test",
                password=SecretStr("short"),
                roles=["extension_worker"],
                reason="synthetic weak password test",
            ),
        )
    assert weak.value.code == "weak_password"

    provision_staff(service, clock, admin)
    with pytest.raises(ApiError) as duplicate:
        provision_staff(service, clock, admin)
    assert duplicate.value.code == "email_in_use"


def test_role_change_increments_token_version_and_rejects_old_refresh() -> None:
    service, _, clock = make_identity_service()
    bootstrap_admin(service)
    admin = admin_context(service, clock)
    provisioned = provision_staff(service, clock, admin, roles=["extension_worker"])
    assert provisioned.mfa_secret is not None
    worker_tokens = login(
        service,
        clock,
        email=STAFF_EMAIL,
        totp_secret=provisioned.mfa_secret,
    )
    worker = service.store.user_by_email(STAFF_EMAIL)
    assert worker is not None

    updated = service.change_roles(
        admin,
        worker.user_id,
        RoleUpdateRequest(roles=["agronomist"], reason="synthetic role change test"),
    )

    assert updated.roles == ["agronomist"]
    with pytest.raises(ApiError) as refresh_error:
        service.refresh(worker_tokens.refresh_token)
    assert refresh_error.value.code == "token_version_changed"
    with pytest.raises(ApiError) as access_error:
        service.resolve_access_token(worker_tokens.access_token)
    assert access_error.value.code == "forbidden"


def test_role_requiring_mfa_cannot_be_assigned_without_a_secret() -> None:
    service, _, clock = make_identity_service()
    bootstrap_admin(service)
    admin = admin_context(service, clock)
    provisioned = provision_staff(
        service,
        clock,
        admin,
        roles=["extension_worker"],
        require_mfa=False,
    )

    with pytest.raises(ApiError) as error:
        service.change_roles(
            admin,
            provisioned.user.user_id,
            RoleUpdateRequest(
                roles=["pathologist"],
                reason="synthetic missing-MFA role change",
            ),
        )
    assert error.value.code == "mfa_not_provisioned"


def test_admin_cannot_change_own_roles_or_promote_a_farmer() -> None:
    service, sender, clock = make_identity_service()
    bootstrap_admin(service)
    admin = admin_context(service, clock)
    farmer = farmer_context(service, sender)

    with pytest.raises(ApiError) as own:
        service.change_roles(
            admin,
            admin.user.user_id,
            RoleUpdateRequest(roles=["pathologist"], reason="synthetic own-role test"),
        )
    assert own.value.code == "cannot_change_own_roles"

    with pytest.raises(ApiError) as farmer_target:
        service.change_roles(
            admin,
            farmer.user.user_id,
            RoleUpdateRequest(roles=["extension_worker"], reason="synthetic farmer target"),
        )
    assert farmer_target.value.code == "invalid_target"


def test_disabling_staff_revokes_sessions_and_blocks_login() -> None:
    service, _, clock = make_identity_service()
    bootstrap_admin(service)
    admin = admin_context(service, clock)
    provision_staff(service, clock, admin, roles=["extension_worker"], require_mfa=False)
    worker_tokens = login(service, clock, email=STAFF_EMAIL)
    worker = service.store.user_by_email(STAFF_EMAIL)
    assert worker is not None

    updated = service.set_user_status(
        admin,
        worker.user_id,
        UserStatusUpdate(status="disabled", reason="synthetic staff departure"),
    )

    assert updated.status == "disabled"
    with pytest.raises(ApiError) as refresh_error:
        service.refresh(worker_tokens.refresh_token)
    assert refresh_error.value.code == "token_invalid"
    with pytest.raises(ApiError) as login_error:
        service.login_staff(LoginRequest(email=STAFF_EMAIL, password=SecretStr(PASSWORD)))
    assert login_error.value.code == "invalid_credentials"


def test_admin_cannot_disable_self_or_the_last_admin() -> None:
    service, _, clock = make_identity_service()
    bootstrap_admin(service)
    admin = admin_context(service, clock)

    with pytest.raises(ApiError) as own:
        service.set_user_status(
            admin,
            admin.user.user_id,
            UserStatusUpdate(status="disabled", reason="synthetic self-disable test"),
        )
    assert own.value.code == "cannot_change_own_status"


def test_admin_record_view_requires_reason_and_audits_before_returning() -> None:
    service, sender, clock = make_identity_service()
    bootstrap_admin(service)
    admin = admin_context(service, clock)
    farmer = farmer_context(service, sender)

    with pytest.raises(ApiError) as short_reason:
        service.admin_view_user(admin, farmer.user.user_id, "short")
    assert short_reason.value.code == "reason_required"

    detail = service.admin_view_user(admin, farmer.user.user_id, "synthetic case review")

    assert detail.user_id == farmer.user.user_id
    assert detail.phone_masked == "+10******001"
    event = service.audit_events()[-1]
    assert event.event_type == "admin.record_viewed"
    assert event.actor_id == admin.user.user_id
    assert event.detail["reason"] == "synthetic case review"


def test_audit_details_never_contain_emails_passwords_or_mfa_secrets() -> None:
    service, _, clock = make_identity_service()
    bootstrap_admin(service)
    admin = admin_context(service, clock)
    provisioned = provision_staff(service, clock, admin, roles=["pathologist"])
    assert provisioned.mfa_secret is not None

    serialised = " ".join(event.model_dump_json() for event in service.audit_events())
    assert ADMIN_EMAIL not in serialised
    assert STAFF_EMAIL not in serialised
    assert PASSWORD not in serialised
    assert TOTP_SECRET not in serialised
    assert provisioned.mfa_secret not in serialised


def test_admin_aggregate_export_has_a_purpose_and_no_pii() -> None:
    service, sender, clock = make_identity_service()
    bootstrap_admin(service)
    admin = admin_context(service, clock)
    farmer_context(service, sender)

    summary = service.export_aggregates(
        admin,
        AdminExportRequest(purpose="synthetic district reporting", row_limit=100),
    )

    assert summary.total_users == 2
    assert summary.counts_by_role["farmer"] == 1
    assert summary.counts_by_role["admin"] == 1
    assert summary.counts_by_status["active"] == 2
    # The note text mentions "phone numbers" and "email addresses", so assert on
    # structure and actual values rather than a substring of the whole payload.
    assert "phone" not in summary.model_dump()
    assert "email" not in summary.model_dump()
    serialised = summary.model_dump_json()
    assert FARMER_PHONE not in serialised
    assert ADMIN_EMAIL not in serialised
    event = service.audit_events()[-1]
    assert event.event_type == "export.generated"
    assert event.detail["purpose"] == "synthetic district reporting"


def test_admin_export_respects_the_row_limit() -> None:
    service, sender, clock = make_identity_service()
    bootstrap_admin(service)
    admin = admin_context(service, clock)
    farmer_context(service, sender)

    with pytest.raises(ApiError) as error:
        service.export_aggregates(
            admin,
            AdminExportRequest(purpose="synthetic small-row export", row_limit=1),
        )
    assert error.value.code == "row_limit_exceeded"


def test_farmer_cannot_call_admin_service_methods() -> None:
    service, sender, clock = make_identity_service()
    bootstrap_admin(service)
    farmer = farmer_context(service, sender)

    with pytest.raises(ApiError) as error:
        service.list_users(farmer)
    assert error.value.code == "forbidden"


def test_staff_with_multiple_roles_can_select_an_explicit_active_role() -> None:
    service, _, clock = make_identity_service()
    bootstrap_admin(service)
    admin = admin_context(service, clock)
    provisioned = provision_staff(
        service,
        clock,
        admin,
        roles=["extension_worker", "pathologist"],
    )
    assert provisioned.mfa_secret is not None

    response = service.login_staff(
        LoginRequest(
            email=STAFF_EMAIL,
            password=SecretStr(PASSWORD),
            role="pathologist",
        )
    )
    assert response.challenge_token is not None
    tokens = service.verify_mfa(
        response.challenge_token,
        totp_code(provisioned.mfa_secret, clock.now),
    )

    assert tokens.role == "pathologist"
    assert isinstance(service.resolve_access_token(tokens.access_token), AuthContext)

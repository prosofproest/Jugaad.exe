"""HTTP contract for auth, self-service and admin identity routes (spec 03 §8)."""

from __future__ import annotations

import pytest
from app.main import app
from app.modules.identity.dependencies import set_identity_service
from fastapi.testclient import TestClient

from tests.support_identity import (
    FARMER_PHONE,
    STAFF_EMAIL,
    admin_context,
    bootstrap_admin,
    farmer_tokens,
    login,
    make_identity_service,
    provision_staff,
)

client = TestClient(app)


@pytest.fixture
def identity():
    service, sender, clock = make_identity_service()
    bootstrap_admin(service)
    set_identity_service(service)
    yield service, sender, clock
    set_identity_service(None)


def _admin_headers(service, clock) -> dict[str, str]:
    tokens = login(service, clock)
    return {"Authorization": f"Bearer {tokens.access_token}"}


def _farmer_headers(service, sender) -> dict[str, str]:
    tokens = farmer_tokens(service, sender)
    return {"Authorization": f"Bearer {tokens.access_token}"}


def test_identity_routes_are_published_with_bearer_security() -> None:
    schema = client.get("/openapi.json").json()

    for path in (
        "/v1/auth/otp/request",
        "/v1/auth/otp/verify",
        "/v1/auth/login",
        "/v1/auth/mfa/verify",
        "/v1/auth/refresh",
        "/v1/auth/logout",
        "/v1/auth/logout-all",
        "/v1/me",
        "/v1/me/consents",
        "/v1/me/export",
        "/v1/me/privacy-requests",
        "/v1/admin/users",
        "/v1/admin/users/{user_id}",
        "/v1/admin/users/{user_id}/roles",
        "/v1/admin/users/{user_id}/status",
        "/v1/admin/maintenance/retention",
        "/v1/admin/exports",
    ):
        assert path in schema["paths"], path

    assert "HTTPBearer" in schema["components"]["securitySchemes"]
    assert schema["paths"]["/v1/me"]["get"]["security"] == [{"HTTPBearer": []}]
    assert schema["paths"]["/v1/auth/otp/request"]["post"].get("security") is None


def test_protected_routes_reject_a_missing_token() -> None:
    for path in ("/v1/me", "/v1/admin/users"):
        response = client.get(path)
        assert response.status_code == 401
        assert response.json()["code"] == "authentication_required"


def test_farmer_can_read_own_profile_but_not_the_admin_surface(identity) -> None:
    service, sender, _ = identity
    headers = _farmer_headers(service, sender)

    profile = client.get("/v1/me", headers=headers)
    admin = client.get("/v1/admin/users", headers=headers)

    assert profile.status_code == 200
    body = profile.json()
    assert body["phone"] == FARMER_PHONE
    assert body["roles"] == ["farmer"]
    assert "password_hash" not in body
    assert "mfa_secret" not in body
    assert admin.status_code == 403
    assert admin.json()["code"] == "forbidden"


def test_otp_http_flow_never_returns_the_code(identity) -> None:
    service, sender, _ = identity

    requested = client.post("/v1/auth/otp/request", json={"phone": FARMER_PHONE})
    code = sender.last_code(FARMER_PHONE)

    assert requested.status_code == 202
    assert code is not None
    assert code not in requested.text
    verified = client.post("/v1/auth/otp/verify", json={"phone": FARMER_PHONE, "code": code})
    assert verified.status_code == 200
    assert verified.json()["role"] == "farmer"
    access = verified.json()["access_token"]
    assert client.get("/v1/me", headers={"Authorization": f"Bearer {access}"}).status_code == 200


def test_consent_routes_record_and_return_the_catalog(identity) -> None:
    service, sender, _ = identity
    headers = _farmer_headers(service, sender)

    before = client.get("/v1/me/consents", headers=headers)
    updated = client.post(
        "/v1/me/consents",
        headers=headers,
        json={
            "decisions": [
                {"consent_type": "service_privacy", "granted": True},
                {"consent_type": "image_assessment", "granted": True},
                {"consent_type": "approximate_location", "granted": True},
            ],
            "channel": "web-test",
        },
    )

    assert before.status_code == 200
    assert before.json()["consent_complete"] is False
    assert updated.status_code == 200
    assert updated.json()["consent_complete"] is True
    assert updated.json()["states"][0]["recorded_at"] is not None


def test_admin_record_view_requires_a_reason_and_never_returns_raw_phone(identity) -> None:
    service, sender, clock = identity
    farmer_headers = _farmer_headers(service, sender)
    farmer = client.get("/v1/me", headers=farmer_headers).json()
    headers = _admin_headers(service, clock)

    missing = client.get(f"/v1/admin/users/{farmer['user_id']}", headers=headers)
    short = client.get(
        f"/v1/admin/users/{farmer['user_id']}",
        headers=headers,
        params={"reason": "short"},
    )
    viewed = client.get(
        f"/v1/admin/users/{farmer['user_id']}",
        headers=headers,
        params={"reason": "synthetic web review"},
    )

    assert missing.status_code == 422
    assert short.status_code == 400
    assert short.json()["code"] == "reason_required"
    assert viewed.status_code == 200
    body = viewed.json()
    assert body["phone_masked"] == "+10******001"
    assert FARMER_PHONE not in viewed.text
    assert service.audit_events()[-1].event_type == "admin.record_viewed"


def test_admin_can_provision_staff_and_change_roles_over_http(identity) -> None:
    service, _, clock = identity
    headers = _admin_headers(service, clock)

    created = client.post(
        "/v1/admin/users",
        headers=headers,
        json={
            "email": STAFF_EMAIL,
            "password": "correct horse battery staple",
            "roles": ["extension_worker"],
            "require_mfa": True,
            "reason": "synthetic web provisioning",
        },
    )

    assert created.status_code == 201
    body = created.json()
    assert body["user"]["email"] == STAFF_EMAIL
    assert "note" in body
    user_id = body["user"]["user_id"]
    changed = client.patch(
        f"/v1/admin/users/{user_id}/roles",
        headers=headers,
        json={"roles": ["agronomist"], "reason": "synthetic web role change"},
    )
    assert changed.status_code == 200
    assert changed.json()["roles"] == ["agronomist"]
    assert any(event.event_type == "user.role_changed" for event in service.audit_events())


def test_admin_aggregate_export_requires_purpose_and_contains_no_pii(identity) -> None:
    service, sender, clock = identity
    _farmer_headers(service, sender)
    headers = _admin_headers(service, clock)

    missing = client.post(
        "/v1/admin/exports",
        headers=headers,
        json={"purpose": "short"},
    )
    exported = client.post(
        "/v1/admin/exports",
        headers=headers,
        json={"purpose": "synthetic web district report", "row_limit": 100},
    )

    assert missing.status_code == 422
    assert exported.status_code == 200
    body = exported.json()
    assert body["total_users"] == 2
    assert body["counts_by_role"]["farmer"] == 1
    assert FARMER_PHONE not in exported.text
    assert "@" not in exported.text
    assert service.audit_events()[-1].event_type == "export.generated"


def test_logout_ends_the_session_over_http(identity) -> None:
    service, sender, _ = identity
    headers = _farmer_headers(service, sender)

    logged_out = client.post("/v1/auth/logout", headers=headers)
    profile = client.get("/v1/me", headers=headers)

    assert logged_out.status_code == 204
    assert profile.status_code == 401
    assert profile.json()["code"] == "token_invalid"


def test_account_deletion_requires_confirmation_and_soft_deletes(identity) -> None:
    service, sender, _ = identity
    headers = _farmer_headers(service, sender)

    wrong = client.request(
        "DELETE",
        "/v1/me",
        headers=headers,
        json={"confirmation": "delete", "reason": "synthetic http deletion"},
    )
    deleted = client.request(
        "DELETE",
        "/v1/me",
        headers=headers,
        json={"confirmation": "DELETE", "reason": "synthetic http deletion"},
    )

    assert wrong.status_code == 400
    assert wrong.json()["code"] == "deletion_confirmation_required"
    assert deleted.status_code == 200
    assert deleted.json()["hard_delete_after"] is None
    assert client.get("/v1/me", headers=headers).status_code == 401


def test_privacy_request_round_trip_over_http(identity) -> None:
    service, sender, _ = identity
    headers = _farmer_headers(service, sender)

    created = client.post(
        "/v1/me/privacy-requests",
        headers=headers,
        json={
            "kind": "access",
            "detail": "Synthetic access request for API coverage.",
            "reason": "synthetic web privacy test",
        },
    )
    listed = client.get("/v1/me/privacy-requests", headers=headers)

    assert created.status_code == 201
    assert created.json()["status"] == "queued"
    assert listed.status_code == 200
    assert [item["request_id"] for item in listed.json()] == [created.json()["request_id"]]


def test_admin_status_route_disables_staff(identity) -> None:
    service, _, clock = identity
    admin = admin_context(service, clock)
    provisioned = provision_staff(service, clock, admin, require_mfa=False)
    headers = _admin_headers(service, clock)

    disabled = client.patch(
        f"/v1/admin/users/{provisioned.user.user_id}/status",
        headers=headers,
        json={"status": "disabled", "reason": "synthetic web departure"},
    )

    assert disabled.status_code == 200
    assert disabled.json()["status"] == "disabled"
    assert service.audit_events()[-1].event_type == "user.disabled"

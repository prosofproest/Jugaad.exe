"""Synthetic identity fixtures.

All phones use the ``+100000000xx`` range, all emails use ``.test`` and all
passwords/TOTP seeds exist only for this test suite. Nothing here is real user
data or a production credential.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.modules.identity.models import LoginRequest, LoginResponse, TokenPair
from app.modules.identity.security import totp_code
from app.modules.identity.service import AuthContext, IdentityService, MemoryOtpSender
from pydantic import SecretStr

SECRET = "synthetic-test-secret-with-at-least-32-characters"
PASSWORD = "correct horse battery staple"
TOTP_SECRET = "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"
ADMIN_EMAIL = "admin@example.test"
STAFF_EMAIL = "reviewer@example.test"
FARMER_PHONE = "+10000000001"
OTHER_FARMER_PHONE = "+10000000002"
FIXED_NOW = datetime(2026, 11, 6, 6, 0, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self, start: datetime = FIXED_NOW) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs: float) -> datetime:
        self.now += timedelta(**kwargs)
        return self.now


def make_identity_service() -> tuple[IdentityService, MemoryOtpSender, FakeClock]:
    sender = MemoryOtpSender()
    clock = FakeClock()
    service = IdentityService(
        secret=SECRET,
        clock=clock,
        otp_sender=sender,
    )
    return service, sender, clock


def bootstrap_admin(service: IdentityService) -> None:
    service.bootstrap_admin(ADMIN_EMAIL, PASSWORD, TOTP_SECRET)


def login(
    service: IdentityService,
    clock: FakeClock,
    *,
    email: str = ADMIN_EMAIL,
    password: str = PASSWORD,
    totp_secret: str = TOTP_SECRET,
) -> TokenPair:
    response: LoginResponse = service.login_staff(
        LoginRequest(email=email, password=SecretStr(password))
    )
    if response.mfa_required:
        assert response.challenge_token is not None
        return service.verify_mfa(
            response.challenge_token,
            totp_code(totp_secret, clock.now),
        )
    assert response.tokens is not None
    return response.tokens


def admin_context(service: IdentityService, clock: FakeClock) -> AuthContext:
    return service.resolve_access_token(login(service, clock).access_token)


def farmer_tokens(
    service: IdentityService,
    sender: MemoryOtpSender,
    *,
    phone: str = FARMER_PHONE,
) -> TokenPair:
    service.request_otp(phone)
    code = sender.last_code(phone)
    assert code is not None
    return service.verify_otp(phone, code)


def farmer_context(
    service: IdentityService,
    sender: MemoryOtpSender,
    *,
    phone: str = FARMER_PHONE,
) -> AuthContext:
    return service.resolve_access_token(farmer_tokens(service, sender, phone=phone).access_token)


def provision_staff(
    service: IdentityService,
    clock: FakeClock,
    actor: AuthContext,
    *,
    email: str = STAFF_EMAIL,
    roles: list[str] | None = None,
    require_mfa: bool = True,
):
    from app.modules.identity.models import StaffCreateRequest

    return service.provision_staff(
        actor,
        StaffCreateRequest(
            email=email,
            password=SecretStr(PASSWORD),
            roles=roles or ["extension_worker"],
            require_mfa=require_mfa,
            reason="synthetic provisioning for tests",
        ),
    )

"""Dependency wiring for identity routes.

The service is a process singleton built from ``Settings``. Tests replace it
with ``set_identity_service``; every protected route resolves the caller through
``get_current_context`` so an unauthenticated request is denied by default.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from threading import Lock

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.modules.identity.models import Role
from app.modules.identity.security import totp_code
from app.modules.identity.service import (
    AuthContext,
    IdentityService,
    MemoryOtpSender,
    UnconfiguredOtpSender,
)
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_DEFAULT_DEV_SECRET = "dev-only-insecure-secret-change-me"

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Access token issued by an OTP, staff login or MFA verification.",
)

_service: IdentityService | None = None
_service_lock = Lock()


def _bootstrap_settings(settings: Settings) -> tuple[str, str, str] | None:
    values = (
        settings.auth_bootstrap_admin_email,
        settings.auth_bootstrap_admin_password,
        settings.auth_bootstrap_admin_totp_secret,
    )
    supplied = [value for value in values if value]
    if not supplied:
        return None
    if len(supplied) != len(values):
        raise RuntimeError("Identity bootstrap requires email, password and TOTP secret together.")
    email, password, secret = (value or "" for value in values)
    try:
        totp_code(secret, datetime.now(UTC))
    except (ValueError, TypeError) as error:
        raise RuntimeError("Identity bootstrap TOTP secret is not valid base32.") from error
    return email, password, secret


def build_identity_service(settings: Settings | None = None) -> IdentityService:
    """Build the service from deployment settings and fail closed on misconfiguration."""

    settings = settings or get_settings()
    secret = settings.auth_secret
    if settings.is_production:
        if secret == _DEFAULT_DEV_SECRET:
            raise RuntimeError("APP_AUTH_SECRET must be replaced before running in production.")
        if len(secret) < 32:
            raise RuntimeError("APP_AUTH_SECRET must contain at least 32 characters.")

    # There is no approved SMS provider yet (spec 03 Q1). Local/tests use the
    # memory adapter so codes never leave the process; production fails closed
    # rather than pretending a code was delivered.
    sender = UnconfiguredOtpSender() if settings.is_production else MemoryOtpSender()
    retention = (
        timedelta(days=settings.auth_deletion_retention_days)
        if settings.auth_deletion_retention_days is not None
        else None
    )
    service = IdentityService(
        secret=secret,
        otp_sender=sender,
        access_ttl=timedelta(minutes=settings.auth_access_ttl_minutes),
        refresh_ttl=timedelta(days=settings.auth_refresh_ttl_days),
        mfa_challenge_ttl=timedelta(minutes=settings.auth_mfa_challenge_ttl_minutes),
        otp_ttl=timedelta(minutes=settings.auth_otp_ttl_minutes),
        otp_max_attempts=settings.auth_otp_max_attempts,
        otp_phone_limit=settings.auth_otp_phone_limit,
        otp_ip_limit=settings.auth_otp_ip_limit,
        otp_rate_window=timedelta(minutes=settings.auth_otp_rate_window_minutes),
        staff_failure_limit=settings.auth_staff_failure_limit,
        staff_lockout=timedelta(minutes=settings.auth_staff_lockout_minutes),
        deletion_retention=retention,
    )
    bootstrap = _bootstrap_settings(settings)
    if bootstrap is not None:
        try:
            service.bootstrap_admin(*bootstrap)
        except ApiError as error:
            raise RuntimeError(
                f"Identity bootstrap rejected by the service ({error.code})."
            ) from error
    return service


def get_identity_service() -> IdentityService:
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = build_identity_service()
    return _service


def set_identity_service(service: IdentityService | None) -> None:
    """Test/DI hook; ``None`` restores lazy construction from settings."""

    global _service
    with _service_lock:
        _service = service


def get_current_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    service: IdentityService = Depends(get_identity_service),
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError(
            code="authentication_required",
            title="Authentication required",
            status=401,
            detail="Send a bearer access token.",
        )
    return service.resolve_access_token(credentials.credentials)


def require_roles(*allowed: Role) -> Callable[..., AuthContext]:
    """Deny by default: a route must name every role it accepts."""

    def dependency(context: AuthContext = Depends(get_current_context)) -> AuthContext:
        if context.role not in allowed:
            raise ApiError(
                code="forbidden",
                title="Forbidden",
                status=403,
                detail="Your active role cannot perform this action.",
            )
        return context

    return dependency


def require_required_consents(
    context: AuthContext = Depends(get_current_context),
    service: IdentityService = Depends(get_identity_service),
) -> AuthContext:
    """Use on report-creating routes so missing consent is refused server-side."""

    service.assert_required_consents(context.user.user_id)
    return context

"""Identity, authentication, sessions and consent."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError
from app.core.rate_limit import get_limiter
from app.core.security import (
    create_access_token,
    create_mfa_challenge,
    decode_mfa_challenge,
    decode_token,
    generate_otp,
    generate_refresh_token,
    hash_otp,
    hash_password,
    hash_refresh_token,
    new_totp_secret,
    TokenError,
    totp_uri,
    verify_otp_hash,
    verify_password,
    verify_totp,
)
from app.db.base import new_id
from app.db.models import (
    Consent,
    OtpCode,
    Session as AuthSession,
    User,
    UserAreaAssignment,
    UserPermission,
    UserRole,
)
from app.modules.audit.service import record_audit

REQUIRED_CONSENTS = ("service_terms", "image_use", "approximate_location")
OPTIONAL_CONSENTS = ("research", "extension_contact")
ALL_CONSENTS = REQUIRED_CONSENTS + OPTIONAL_CONSENTS
CONSENT_TEXTS = {
    "service_terms": "I accept the service terms and privacy notice.",
    "image_use": "My photo may be analysed and stored with this case.",
    "approximate_location": "My approximate block-level area may be used.",
    "research": "I optionally allow de-identified use for model improvement.",
    "extension_contact": "An extension worker may contact me about a case.",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_phone(raw: str) -> str:
    value = re.sub(r"[^\d+]", "", raw or "")
    if not value:
        raise ApiError(422, "invalid_phone", "A phone number is required")
    if value.startswith("+"):
        candidate = value
    elif len(value) == 10:
        candidate = f"+91{value}"
    elif len(value) == 12 and value.startswith("91"):
        candidate = f"+{value}"
    else:
        candidate = f"+{value}"
    if not re.fullmatch(r"\+[1-9]\d{7,14}", candidate):
        raise ApiError(422, "invalid_phone", "Phone number must be in E.164 form")
    return candidate


def _current_consent_version() -> str:
    return "consent-2026-11"


def _consent_hash(consent_type: str, version: str) -> str:
    text = f"{consent_type}:{version}:{CONSENT_TEXTS.get(consent_type, '')}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def active_roles(db: Session, user_id: str) -> list[str]:
    rows = db.scalars(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.revoked_at.is_(None))
    ).all()
    return [row.role_code for row in rows]


def active_permissions(db: Session, user_id: str) -> set[str]:
    rows = db.scalars(
        select(UserPermission).where(
            UserPermission.user_id == user_id, UserPermission.revoked_at.is_(None)
        )
    ).all()
    return {row.permission for row in rows}


def missing_required_consents(db: Session, user_id: str) -> list[str]:
    version = _current_consent_version()
    missing: list[str] = []
    for consent_type in REQUIRED_CONSENTS:
        row = db.scalar(
            select(Consent)
            .where(
                Consent.user_id == user_id,
                Consent.type == consent_type,
                Consent.version == version,
            )
            .order_by(Consent.created_at.desc())
        )
        if row is None or not row.granted:
            missing.append(consent_type)
    return missing


def consent_snapshot(db: Session, user_id: str) -> list[dict]:
    rows = db.scalars(
        select(Consent).where(Consent.user_id == user_id).order_by(Consent.created_at.desc())
    ).all()
    latest: dict[str, Consent] = {}
    for row in rows:
        latest.setdefault(row.type, row)
    return [
        {
            "type": row.type,
            "version": row.version,
            "granted": row.granted,
            "channel": row.channel,
            "created_at": row.created_at.isoformat(),
        }
        for row in latest.values()
    ]


def grant_consent(
    db: Session, user: User, *, consent_type: str, granted: bool, channel: str = "app"
) -> Consent:
    if consent_type not in ALL_CONSENTS:
        raise ApiError(422, "invalid_consent_type", "Unknown consent type")
    version = _current_consent_version()
    record = Consent(
        user_id=user.id,
        type=consent_type,
        version=version,
        granted=granted,
        text_hash=_consent_hash(consent_type, version),
        channel=channel,
    )
    db.add(record)
    record_audit(
        db,
        action="consent.granted" if granted else "consent.withdrawn",
        actor=user,
        entity_type="user",
        entity_id=user.id,
        detail={"consent_type": consent_type, "version": version},
    )
    return record


def _ensure_farmer(db: Session, phone: str) -> User:
    user = db.scalar(select(User).where(User.phone_e164 == phone))
    if user is not None:
        if user.status != "active" or user.deleted_at is not None:
            raise ApiError(403, "account_disabled", "This account is not active")
        return user
    user = User(
        phone_e164=phone,
        display_name=None,
        active_role="farmer",
        locale="en",
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_code="farmer", granted_by="self"))
    return user


def request_otp(db: Session, *, phone: str, ip: str | None) -> dict:
    settings = get_settings()
    phone_e164 = normalize_phone(phone)
    limiter = get_limiter()
    limiter.check(f"otp:{phone_e164}")
    if ip:
        limiter.check(f"otp-ip:{ip}")

    code = generate_otp()
    otp = OtpCode(
        phone_e164=phone_e164,
        code_hash=hash_otp(phone_e164, code),
        expires_at=_now() + timedelta(minutes=settings.otp_ttl_minutes),
    )
    db.add(otp)
    # Delivery is a development stub: no SMS provider is configured. The code is
    # only echoed when explicitly enabled outside production.
    result: dict = {
        "message": "If this number is registered, a code was sent.",
        "expires_in_seconds": settings.otp_ttl_minutes * 60,
        "delivery": "development_stub" if not settings.is_production else "sms",
    }
    if settings.expose_otp_in_dev and not settings.is_production:
        result["dev_code"] = code
    return result


def verify_otp(
    db: Session,
    *,
    phone: str,
    code: str,
    device_id: str | None,
    user_agent: str | None,
    ip_hash: str | None,
) -> dict:
    settings = get_settings()
    phone_e164 = normalize_phone(phone)
    otp = db.scalar(
        select(OtpCode)
        .where(OtpCode.phone_e164 == phone_e164, OtpCode.consumed_at.is_(None))
        .order_by(OtpCode.created_at.desc())
    )
    if otp is None or otp.expires_at <= _now():
        raise ApiError(401, "otp_expired", "That code has expired; request a new one")
    if otp.attempts >= settings.otp_max_attempts:
        raise ApiError(429, "otp_rate_limited", "Too many attempts; request a new code")
    otp.attempts += 1
    db.flush()
    if not verify_otp_hash(phone_e164, code, otp.code_hash):
        raise ApiError(401, "invalid_otp", "The code is not correct")

    otp.consumed_at = _now()
    user = _ensure_farmer(db, phone_e164)
    if device_id and not user.id:
        raise ApiError(500, "internal_error", "User creation failed")
    tokens = issue_tokens(db, user, user_agent=user_agent, ip_hash=ip_hash)
    tokens["consent_required"] = bool(missing_required_consents(db, user.id))
    record_audit(
        db,
        action="auth.login_succeeded",
        actor=user,
        entity_type="user",
        entity_id=user.id,
        detail={"method": "otp"},
    )
    return tokens


def _lockout_check(user: User) -> None:
    if user.locked_until and user.locked_until > _now():
        raise ApiError(423, "account_locked", "Account is temporarily locked")


def _record_failed_login(db: Session, user: User) -> None:
    now = _now()
    window = timedelta(minutes=15)
    if user.failed_login_first_at is None or now - user.failed_login_first_at > window:
        user.failed_login_first_at = now
        user.failed_login_count = 0
    user.failed_login_count += 1
    if user.failed_login_count >= 10:
        user.locked_until = now + window
    record_audit(
        db,
        action="auth.login_failed",
        actor_id=user.id,
        actor_role=user.active_role,
        entity_type="user",
        entity_id=user.id,
    )


def login(
    db: Session,
    *,
    email: str,
    password: str,
    user_agent: str | None,
    ip_hash: str | None,
) -> dict:
    email_normalized = (email or "").strip().lower()
    user = db.scalar(select(User).where(User.email == email_normalized))
    if user is None:
        # Same response time and message shape as a wrong password.
        raise ApiError(401, "invalid_credentials", "Email or password is incorrect")
    _lockout_check(user)
    if user.status != "active" or user.deleted_at is not None:
        raise ApiError(403, "account_disabled", "This account is not active")
    if not verify_password(password, user.password_hash):
        _record_failed_login(db, user)
        raise ApiError(401, "invalid_credentials", "Email or password is incorrect")

    user.failed_login_count = 0
    user.failed_login_first_at = None
    user.locked_until = None

    roles = active_roles(db, user.id)
    permissions = active_permissions(db, user.id)
    mfa_required = "admin" in roles or "can_confirm" in permissions
    if mfa_required:
        if not user.mfa_secret:
            raise ApiError(
                403,
                "mfa_not_configured",
                "Multi-factor authentication must be configured for this account",
            )
        record_audit(
            db,
            action="auth.mfa_challenged",
            actor=user,
            entity_type="user",
            entity_id=user.id,
        )
        return {
            "mfa_required": True,
            "challenge": create_mfa_challenge(user_id=user.id),
            "expires_in_seconds": get_settings().mfa_challenge_minutes * 60,
        }

    tokens = issue_tokens(db, user, user_agent=user_agent, ip_hash=ip_hash)
    tokens["consent_required"] = bool(missing_required_consents(db, user.id))
    record_audit(
        db,
        action="auth.login_succeeded",
        actor=user,
        entity_type="user",
        entity_id=user.id,
        detail={"method": "password"},
    )
    return tokens


def verify_mfa(
    db: Session,
    *,
    challenge: str,
    totp: str,
    user_agent: str | None,
    ip_hash: str | None,
) -> dict:
    try:
        payload = decode_mfa_challenge(challenge)
    except TokenError as error:
        raise ApiError(401, error.code, "MFA challenge is invalid") from error
    user = db.get(User, payload.get("sub", ""))
    if user is None or user.status != "active" or user.deleted_at is not None:
        raise ApiError(401, "unauthorized", "Account is not active")
    if not verify_totp(user.mfa_secret, totp):
        record_audit(
            db,
            action="auth.mfa_failed",
            actor=user,
            entity_type="user",
            entity_id=user.id,
        )
        raise ApiError(401, "invalid_mfa", "The authentication code is not correct")
    tokens = issue_tokens(db, user, user_agent=user_agent, ip_hash=ip_hash)
    tokens["consent_required"] = bool(missing_required_consents(db, user.id))
    record_audit(
        db,
        action="auth.login_succeeded",
        actor=user,
        entity_type="user",
        entity_id=user.id,
        detail={"method": "password+mfa"},
    )
    return tokens


def issue_tokens(
    db: Session,
    user: User,
    *,
    user_agent: str | None,
    ip_hash: str | None,
    family_id: str | None = None,
) -> dict:
    settings = get_settings()
    roles = active_roles(db, user.id)
    if not roles:
        raise ApiError(403, "forbidden", "Account has no active role")
    if user.active_role not in roles:
        user.active_role = roles[0]

    refresh = generate_refresh_token()
    session_id = new_id("ses")
    auth_session = AuthSession(
        id=session_id,
        user_id=user.id,
        refresh_hash=hash_refresh_token(refresh),
        family_id=family_id or new_id("fam"),
        token_version=user.token_version,
        expires_at=_now() + timedelta(days=settings.refresh_token_days),
        ip_hash=ip_hash,
        user_agent=user_agent,
    )
    db.add(auth_session)
    access = create_access_token(
        user_id=user.id,
        role=user.active_role,
        session_id=session_id,
        token_version=user.token_version,
    )
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.access_token_minutes * 60,
        "active_role": user.active_role,
        "roles": roles,
        "permissions": sorted(active_permissions(db, user.id)),
        "user": {
            "id": user.id,
            "email": user.email,
            "phone": user.phone_e164,
            "display_name": user.display_name,
            "locale": user.locale,
        },
    }


def refresh_tokens(
    db: Session, *, refresh_token: str, user_agent: str | None, ip_hash: str | None
) -> dict:
    token_hash = hash_refresh_token(refresh_token)
    auth_session = db.scalar(
        select(AuthSession).where(AuthSession.refresh_hash == token_hash)
    )
    if auth_session is None:
        raise ApiError(401, "invalid_token", "Refresh token is invalid")
    if auth_session.revoked_at is not None:
        # Reuse of a rotated token: revoke the whole family.
        for row in db.scalars(
            select(AuthSession).where(AuthSession.family_id == auth_session.family_id)
        ).all():
            if row.revoked_at is None:
                row.revoked_at = _now()
        record_audit(
            db,
            action="auth.token_reuse_detected",
            actor_id=auth_session.user_id,
            entity_type="session",
            entity_id=auth_session.id,
        )
        raise ApiError(401, "token_reused", "Refresh token reuse detected; sign in again")
    if auth_session.expires_at <= _now():
        raise ApiError(401, "token_expired", "Refresh token has expired")

    user = db.get(User, auth_session.user_id)
    if user is None or user.status != "active" or user.deleted_at is not None:
        raise ApiError(401, "unauthorized", "Account is not active")
    if auth_session.token_version != user.token_version:
        auth_session.revoked_at = _now()
        raise ApiError(401, "token_stale", "Sign in again to pick up role changes")

    auth_session.revoked_at = _now()
    tokens = issue_tokens(
        db,
        user,
        user_agent=user_agent,
        ip_hash=ip_hash,
        family_id=auth_session.family_id,
    )
    record_audit(
        db,
        action="auth.token_refreshed",
        actor=user,
        entity_type="session",
        entity_id=auth_session.id,
    )
    return tokens


def logout(db: Session, *, user: User, session_id: str | None) -> None:
    if session_id:
        auth_session = db.get(AuthSession, session_id)
        if auth_session and auth_session.user_id == user.id:
            for row in db.scalars(
                select(AuthSession).where(AuthSession.family_id == auth_session.family_id)
            ).all():
                if row.revoked_at is None:
                    row.revoked_at = _now()


def logout_all(db: Session, *, user: User) -> None:
    for row in db.scalars(
        select(AuthSession).where(
            AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None)
        )
    ).all():
        row.revoked_at = _now()
    record_audit(
        db, action="auth.logout_all", actor=user, entity_type="user", entity_id=user.id
    )


def ensure_mfa_secret(db: Session, user: User) -> tuple[str, str]:
    if user.mfa_secret:
        return user.mfa_secret, totp_uri(user.mfa_secret, user.email or user.id)
    secret = new_totp_secret()
    user.mfa_secret = secret
    return secret, totp_uri(secret, user.email or user.id)


def me_payload(db: Session, user: User) -> dict:
    roles = active_roles(db, user.id)
    areas = db.scalars(
        select(UserAreaAssignment).where(UserAreaAssignment.user_id == user.id)
    ).all()
    return {
        "id": user.id,
        "email": user.email,
        "phone": user.phone_e164,
        "display_name": user.display_name,
        "locale": user.locale,
        "status": user.status,
        "active_role": user.active_role,
        "roles": roles,
        "permissions": sorted(active_permissions(db, user.id)),
        "mfa_enabled": bool(user.mfa_secret),
        "consents": consent_snapshot(db, user.id),
        "missing_required_consents": missing_required_consents(db, user.id),
        "area_assignments": [
            {"geo_code": row.geo_code, "level": row.level} for row in areas
        ],
    }

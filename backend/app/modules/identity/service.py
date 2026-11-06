"""Identity service: phone OTP, staff MFA, sessions, consent, privacy and audit.

Scope boundaries, recorded rather than hidden:

* Storage is process-local. A SQLAlchemy/Alembic implementation is still owed.
* OTP delivery is an injected adapter. The process default is a memory sender used
  by tests and local development; production must supply an SMS adapter.
* Passwords use stdlib ``scrypt``. The spec names Argon2id; changing that needs a
  reviewed dependency, so the deviation is recorded in the tracker.
* Retention of cases, images and derived data is not implemented because D10 is
  open. Only short-lived credentials are purged.
* Existing demo feature routes (chat, assessments, advisories, map) are not
  retrofitted with auth in this slice. New ``/v1/me`` and ``/v1/admin`` routes
  use the deny-by-default dependencies; the gap is recorded in the test matrix.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import uuid4

from app.core.audit import AuditEvent
from app.core.errors import ApiError
from app.modules.identity.models import (
    MFA_REQUIRED_ROLES,
    ROLES,
    STAFF_ROLES,
    AdminExportRequest,
    AdminExportSummary,
    AdminUserDetail,
    ConsentDefinition,
    ConsentOverview,
    ConsentRecord,
    ConsentState,
    ConsentType,
    ConsentUpdate,
    DeletionResult,
    ExportBundle,
    LoginRequest,
    LoginResponse,
    OtpRequested,
    PrivacyRequest,
    PrivacyRequestCreate,
    RetentionResult,
    Role,
    RoleUpdateRequest,
    StaffCreateRequest,
    StaffProvisioned,
    TokenPair,
    User,
    UserProfile,
    UserStatusUpdate,
    UserSummary,
)
from app.modules.identity.security import (
    DEFAULT_SCRYPT,
    AccessTokenCodec,
    ScryptParameters,
    TokenError,
    generate_otp_code,
    generate_refresh_token,
    generate_totp_secret,
    hash_otp,
    hash_password,
    hash_token,
    mask_phone,
    otpauth_uri,
    verify_password,
    verify_totp,
)
from app.modules.identity.store import IdentityStore, OtpChallenge, RefreshTokenRecord

CONSENT_CATALOG_VERSION = "draft-2026-11-06"

_PHONE_RE = re.compile(r"^\+[1-9]\d{6,14}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_CLEAN_RE = re.compile(r"[\s\-().]")
_MIN_PASSWORD_LENGTH = 12

# Deliberately no programme retention values here. D10 is open, so the service
# only accepts a policy supplied by the deployment; ``None`` means "not set".
RETENTION_POLICY_UNSET = None


class OtpDeliveryError(Exception):
    """The configured SMS adapter could not accept the message."""


class OtpSender(Protocol):
    def send(self, phone: str, code: str) -> None: ...


class MemoryOtpSender:
    """Local/test adapter. Holds the code in memory and never returns it via HTTP."""

    def __init__(self) -> None:
        self._messages: list[tuple[str, str]] = []

    def send(self, phone: str, code: str) -> None:
        self._messages.append((phone, code))

    def last_code(self, phone: str) -> str | None:
        for candidate_phone, code in reversed(self._messages):
            if candidate_phone == phone:
                return code
        return None

    def messages(self) -> list[tuple[str, str]]:
        return list(self._messages)


class UnconfiguredOtpSender:
    """Production fail-closed adapter until an SMS provider is wired."""

    def send(self, phone: str, code: str) -> None:
        raise OtpDeliveryError("No OTP delivery provider is configured.")


@dataclass(frozen=True)
class AuthContext:
    """The authenticated caller. ``role`` is the active role from the token."""

    user: User
    role: Role
    session_id: str
    token_version: int


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _hash_consent_text(version: str, title: str, summary: str) -> str:
    material = f"{version}|{title}|{summary}".encode()
    return hashlib.sha256(material).hexdigest()


def default_consent_catalog() -> list[ConsentDefinition]:
    """Plain-language draft consent text.

    The wording is a draft until the data controller and local language are
    confirmed (spec 03 Q3). It never gates optional choices behind required ones.
    """

    version = CONSENT_CATALOG_VERSION
    entries: list[tuple[ConsentType, bool, str, str]] = [
        (
            "service_privacy",
            True,
            "Service terms and privacy",
            (
                "We collect your phone number, the photos you choose to send, the "
                "crop and area you select, and the results we show you. We use them "
                "to provide an assistive photo assessment and to run the service. "
                "You can ask for a copy of your data, withdraw optional consent, or "
                "ask us to delete your account. This is a draft summary until the "
                "data controller and the local language are confirmed."
            ),
        ),
        (
            "image_assessment",
            True,
            "Photos used for assessment",
            (
                "A photo you attach is analysed to suggest what might be visible on "
                "the plant and is stored with the case. It is assistive only: it is "
                "not a diagnosis, and a trained person may review it."
            ),
        ),
        (
            "approximate_location",
            True,
            "Approximate area only",
            (
                "We store a block-level area, not exact farm coordinates. This lets "
                "us show area information without exposing the exact location of "
                "your farm."
            ),
        ),
        (
            "research_model_improvement",
            False,
            "Optional research use",
            (
                "Optional: labelled photos may be used to improve the assessment "
                "model. Saying no does not block photo assessment or reporting, and "
                "you can withdraw at any time."
            ),
        ),
        (
            "extension_worker_contact",
            False,
            "Optional follow-up contact",
            (
                "Optional: an extension worker may contact you about a case you "
                "submit. You can withdraw at any time without losing access."
            ),
        ),
    ]
    return [
        ConsentDefinition(
            consent_type=consent_type,
            required=required,
            version=version,
            title=title,
            summary=summary,
            text_hash=_hash_consent_text(version, title, summary),
        )
        for consent_type, required, title, summary in entries
    ]


class IdentityService:
    def __init__(
        self,
        *,
        secret: str,
        clock: Callable[[], datetime] | None = None,
        store: IdentityStore | None = None,
        otp_sender: OtpSender | None = None,
        consent_catalog: list[ConsentDefinition] | None = None,
        access_ttl: timedelta = timedelta(minutes=15),
        mfa_challenge_ttl: timedelta = timedelta(minutes=5),
        refresh_ttl: timedelta = timedelta(days=30),
        otp_ttl: timedelta = timedelta(minutes=5),
        otp_max_attempts: int = 5,
        otp_phone_limit: int = 5,
        otp_ip_limit: int = 20,
        otp_rate_window: timedelta = timedelta(minutes=15),
        staff_failure_limit: int = 10,
        staff_lockout: timedelta = timedelta(minutes=15),
        scrypt_parameters: ScryptParameters = DEFAULT_SCRYPT,
        deletion_retention: timedelta | None = RETENTION_POLICY_UNSET,
        queued_report_count: Callable[[str], int] | None = None,
    ) -> None:
        self.store = store or IdentityStore()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._secret = secret
        self._otp_sender = otp_sender or MemoryOtpSender()
        self._catalog = consent_catalog or default_consent_catalog()
        self._catalog_by_type = {item.consent_type: item for item in self._catalog}
        self._access_codec = AccessTokenCodec(secret, access_ttl)
        self._mfa_codec = AccessTokenCodec(secret, mfa_challenge_ttl)
        self._access_ttl = access_ttl
        self._mfa_challenge_ttl = mfa_challenge_ttl
        self._refresh_ttl = refresh_ttl
        self._otp_ttl = otp_ttl
        self._otp_max_attempts = otp_max_attempts
        self._otp_phone_limit = otp_phone_limit
        self._otp_ip_limit = otp_ip_limit
        self._otp_rate_window = otp_rate_window
        self._staff_failure_limit = staff_failure_limit
        self._staff_lockout = staff_lockout
        self._scrypt = scrypt_parameters
        self._deletion_retention = deletion_retention
        self._queued_report_count = queued_report_count or (lambda _user_id: 0)

    # -- helpers -------------------------------------------------------

    def _now(self) -> datetime:
        return self._clock()

    def _audit(
        self,
        event_type: str,
        *,
        entity_type: str,
        entity_id: str,
        actor_id: str | None = None,
        detail: dict[str, object] | None = None,
    ) -> AuditEvent:
        return self.store.audit.record(
            event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            detail=detail,
        )

    def _normalise_phone(self, raw: str) -> str:
        cleaned = _PHONE_CLEAN_RE.sub("", raw.strip())
        if not _PHONE_RE.fullmatch(cleaned):
            raise ApiError(
                code="invalid_phone",
                title="Invalid phone number",
                status=422,
                detail="Use an international number such as +10000000001.",
            )
        return cleaned

    def _normalise_email(self, raw: str) -> str:
        cleaned = raw.strip().lower()
        if not _EMAIL_RE.fullmatch(cleaned):
            raise ApiError(
                code="invalid_email",
                title="Invalid email address",
                status=422,
                detail="Enter a valid email address.",
            )
        return cleaned

    def _get_user(self, user_id: str) -> User:
        user = self.store.get_user(user_id)
        if user is None:
            raise ApiError(
                code="user_not_found",
                title="User not found",
                status=404,
                detail="No such user.",
            )
        return user

    def _save(self, user: User, **changes: object) -> User:
        updated = user.model_copy(update={**changes, "updated_at": self._now()})
        return self.store.save_user(updated)

    def _summary(self, user: User) -> UserSummary:
        return UserSummary(
            user_id=user.user_id,
            kind=user.kind,
            roles=list(user.roles),
            status=user.status,
            email=user.email,
            phone_masked=mask_phone(user.phone),
            mfa_enabled=user.mfa_enabled,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def _profile(self, user: User) -> UserProfile:
        return UserProfile(
            **self._summary(user).model_dump(),
            phone=user.phone,
            last_login_at=user.last_login_at,
        )

    def _active_role(self, user: User, requested: Role | None) -> Role:
        if requested is not None:
            if requested not in user.roles:
                raise ApiError(
                    code="invalid_credentials",
                    title="Authentication failed",
                    status=401,
                    detail="Email, password or role is invalid.",
                )
            return requested
        return user.roles[0]

    def _issue_tokens(
        self,
        user: User,
        role: Role,
        *,
        family_id: str | None = None,
        device_id: str | None = None,
    ) -> TokenPair:
        now = self._now()
        session_id = family_id or _id("sess")
        access_token = self._access_codec.issue(
            {
                "typ": "access",
                "sub": user.user_id,
                "role": role,
                "roles": list(user.roles),
                "session_id": session_id,
                "token_version": user.token_version,
            },
            now,
        )
        refresh_plain = generate_refresh_token()
        self.store.add_refresh(
            RefreshTokenRecord(
                token_hash=hash_token(refresh_plain),
                family_id=session_id,
                user_id=user.user_id,
                token_version=user.token_version,
                role=role,
                issued_at=now,
                expires_at=now + self._refresh_ttl,
                device_id=device_id,
            )
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_plain,
            expires_in=int(self._access_ttl.total_seconds()),
            refresh_expires_in=int(self._refresh_ttl.total_seconds()),
            user_id=user.user_id,
            role=role,
        )

    def _mark_login(self, user: User) -> User:
        return self._save(user, last_login_at=self._now(), failed_login_at=[], locked_until=None)

    def _record_failure(self, user: User, now: datetime) -> User:
        window_start = now - self._staff_lockout
        recent = [moment for moment in user.failed_login_at if moment >= window_start]
        recent.append(now)
        locked_until = None
        if len(recent) >= self._staff_failure_limit:
            locked_until = now + self._staff_lockout
        return self._save(user, failed_login_at=recent, locked_until=locked_until)

    def _require_admin(self, actor: AuthContext) -> None:
        current = self.store.get_user(actor.user.user_id)
        if (
            actor.role != "admin"
            or current is None
            or current.status != "active"
            or "admin" not in current.roles
        ):
            raise ApiError(
                code="forbidden",
                title="Forbidden",
                status=403,
                detail="This action requires the admin role.",
            )

    # -- phone OTP -----------------------------------------------------

    def request_otp(self, phone: str, source_ip: str | None = None) -> OtpRequested:
        normalised = self._normalise_phone(phone)
        now = self._now()
        window_start = now - self._otp_rate_window
        phone_key = f"phone:{normalised}"
        ip_key = f"ip:{source_ip or 'unknown'}"
        if self.store.count_otp_requests(phone_key, window_start) >= self._otp_phone_limit:
            raise ApiError(
                code="otp_rate_limited",
                title="Too many code requests",
                status=429,
                detail="Wait before requesting another code.",
                retryable=True,
            )
        if self.store.count_otp_requests(ip_key, window_start) >= self._otp_ip_limit:
            raise ApiError(
                code="otp_rate_limited",
                title="Too many code requests",
                status=429,
                detail="Wait before requesting another code.",
                retryable=True,
            )
        self.store.record_otp_request(phone_key, now)
        self.store.record_otp_request(ip_key, now)

        code = generate_otp_code()
        challenge = OtpChallenge(
            phone=normalised,
            code_hash=hash_otp(code, self._secret),
            created_at=now,
            expires_at=now + self._otp_ttl,
        )
        self.store.put_otp(challenge)
        try:
            self._otp_sender.send(normalised, code)
        except OtpDeliveryError as error:
            self.store.delete_otp(normalised)
            raise ApiError(
                code="otp_delivery_unavailable",
                title="Code delivery unavailable",
                status=503,
                detail="No code was sent. Try again later.",
                retryable=True,
            ) from error
        return OtpRequested()

    def verify_otp(self, phone: str, code: str, device_id: str | None = None) -> TokenPair:
        normalised = self._normalise_phone(phone)
        now = self._now()
        challenge = self.store.get_otp(normalised)
        if challenge is None or challenge.consumed_at is not None:
            raise ApiError(
                code="otp_expired",
                title="Code expired",
                status=400,
                detail="Request a new code.",
            )
        if now >= challenge.expires_at:
            self.store.delete_otp(normalised)
            raise ApiError(
                code="otp_expired",
                title="Code expired",
                status=400,
                detail="Request a new code.",
            )
        if challenge.attempts >= self._otp_max_attempts:
            self.store.delete_otp(normalised)
            raise ApiError(
                code="otp_attempts_exceeded",
                title="Too many attempts",
                status=429,
                detail="Request a new code.",
            )
        challenge.attempts += 1
        self.store.save_otp(challenge)
        import hmac as _hmac

        if not _hmac.compare_digest(hash_otp(code, self._secret), challenge.code_hash):
            self._audit(
                "auth.login_failed",
                entity_type="otp",
                entity_id=normalised[:3] + "***",
                detail={"method": "otp", "reason": "invalid_code"},
            )
            raise ApiError(
                code="invalid_otp",
                title="Invalid code",
                status=400,
                detail="The code is incorrect.",
            )

        challenge.consumed_at = now
        self.store.delete_otp(normalised)
        user = self.store.user_by_phone(normalised)
        created = user is None
        if user is None:
            user = User(
                user_id=_id("usr"),
                kind="farmer",
                phone=normalised,
                roles=["farmer"],
                created_at=now,
                updated_at=now,
            )
            user = self.store.add_user(user)
            self._audit(
                "user.created",
                entity_type="user",
                entity_id=user.user_id,
                actor_id=user.user_id,
                detail={"roles": "farmer", "method": "otp"},
            )
        if user.status != "active":
            raise ApiError(
                code="account_disabled",
                title="Account unavailable",
                status=403,
                detail="This account cannot sign in.",
            )
        # OTP is the farmer sign-in path. A staff/promoted account must not be
        # able to obtain a farmer token (or any token) without its password+MFA.
        if "farmer" not in user.roles:
            raise ApiError(
                code="account_unavailable",
                title="Account unavailable",
                status=403,
                detail="Use the staff sign-in path for this account.",
            )
        user = self._mark_login(user)
        self._audit(
            "auth.login_succeeded",
            entity_type="user",
            entity_id=user.user_id,
            actor_id=user.user_id,
            detail={"method": "otp", "new_user": created},
        )
        return self._issue_tokens(user, "farmer", device_id=device_id)

    # -- staff login and MFA ------------------------------------------

    def login_staff(self, request: LoginRequest) -> LoginResponse:
        email = self._normalise_email(request.email)
        password = request.password.get_secret_value()
        now = self._now()
        user = self.store.user_by_email(email)
        if user is None:
            self._audit(
                "auth.login_failed",
                entity_type="staff_login",
                entity_id="unknown",
                detail={"method": "password", "reason": "unknown_account"},
            )
            raise ApiError(
                code="invalid_credentials",
                title="Authentication failed",
                status=401,
                detail="Email, password or role is invalid.",
            )
        if user.locked_until is not None and now < user.locked_until:
            raise ApiError(
                code="account_locked",
                title="Account locked",
                status=423,
                detail="Too many failed attempts. Ask an admin to unlock the account.",
            )
        if user.status != "active" or user.kind != "staff":
            raise ApiError(
                code="invalid_credentials",
                title="Authentication failed",
                status=401,
                detail="Email, password or role is invalid.",
            )
        if not verify_password(password, user.password_hash, self._scrypt):
            user = self._record_failure(user, now)
            self._audit(
                "auth.login_failed",
                entity_type="user",
                entity_id=user.user_id,
                actor_id=user.user_id,
                detail={
                    "method": "password",
                    "reason": "invalid_password",
                    "locked": user.locked_until is not None,
                },
            )
            if user.locked_until is not None:
                raise ApiError(
                    code="account_locked",
                    title="Account locked",
                    status=423,
                    detail="Too many failed attempts. Ask an admin to unlock the account.",
                )
            raise ApiError(
                code="invalid_credentials",
                title="Authentication failed",
                status=401,
                detail="Email, password or role is invalid.",
            )

        role = self._active_role(user, request.role)
        mfa_required = user.mfa_enabled or role in MFA_REQUIRED_ROLES
        if mfa_required:
            if not user.mfa_secret:
                raise ApiError(
                    code="mfa_not_provisioned",
                    title="MFA not provisioned",
                    status=403,
                    detail="This role requires MFA. Ask an admin to re-provision the account.",
                )
            challenge = self._mfa_codec.issue(
                {
                    "typ": "mfa",
                    "sub": user.user_id,
                    "role": role,
                    "token_version": user.token_version,
                },
                now,
            )
            self._audit(
                "auth.mfa_challenged",
                entity_type="user",
                entity_id=user.user_id,
                actor_id=user.user_id,
                detail={"role": role},
            )
            return LoginResponse(
                mfa_required=True,
                challenge_token=challenge,
                challenge_expires_in=int(self._mfa_challenge_ttl.total_seconds()),
            )

        user = self._mark_login(user)
        self._audit(
            "auth.login_succeeded",
            entity_type="user",
            entity_id=user.user_id,
            actor_id=user.user_id,
            detail={"method": "password", "role": role},
        )
        return LoginResponse(mfa_required=False, tokens=self._issue_tokens(user, role))

    def verify_mfa(self, challenge: str, totp: str) -> TokenPair:
        now = self._now()
        try:
            payload = self._mfa_codec.verify(challenge, now, expected_type="mfa")
        except TokenError as error:
            raise ApiError(
                code=error.code,
                title="MFA challenge invalid",
                status=401,
                detail=error.detail,
            ) from error
        user_id = str(payload.get("sub", ""))
        role = str(payload.get("role", ""))
        user = self.store.get_user(user_id)
        if user is None or user.status != "active" or role not in user.roles:
            raise ApiError(
                code="token_invalid",
                title="Token invalid",
                status=401,
                detail="The challenge is no longer valid.",
            )
        if int(payload.get("token_version", 0)) != user.token_version:
            raise ApiError(
                code="token_version_changed",
                title="Session superseded",
                status=401,
                detail="Sign in again.",
            )
        if not verify_totp(user.mfa_secret, totp, now):
            self._audit(
                "auth.login_failed",
                entity_type="user",
                entity_id=user.user_id,
                actor_id=user.user_id,
                detail={"method": "mfa", "reason": "invalid_totp"},
            )
            raise ApiError(
                code="invalid_credentials",
                title="Authentication failed",
                status=401,
                detail="The authentication code is invalid.",
            )
        user = self._mark_login(user)
        self._audit(
            "auth.login_succeeded",
            entity_type="user",
            entity_id=user.user_id,
            actor_id=user.user_id,
            detail={"method": "mfa", "role": role},
        )
        return self._issue_tokens(user, role)  # type: ignore[arg-type]

    # -- tokens --------------------------------------------------------

    def resolve_access_token(self, token: str) -> AuthContext:
        now = self._now()
        try:
            payload = self._access_codec.verify(token, now, expected_type="access")
        except TokenError as error:
            raise ApiError(
                code=error.code,
                title="Authentication required",
                status=401,
                detail=error.detail,
            ) from error
        user = self.store.get_user(str(payload.get("sub", "")))
        if user is None or user.status != "active":
            raise ApiError(
                code="token_invalid",
                title="Authentication required",
                status=401,
                detail="The account is not active.",
            )
        role = str(payload.get("role", ""))
        if role not in user.roles:
            raise ApiError(
                code="forbidden",
                title="Forbidden",
                status=403,
                detail="The active role is no longer assigned.",
            )
        session_id = str(payload.get("session_id", ""))
        family = self.store.family_tokens(session_id)
        if not family or any(item.revoked_at is not None for item in family):
            raise ApiError(
                code="token_invalid",
                title="Authentication required",
                status=401,
                detail="The session has ended.",
            )
        return AuthContext(
            user=user,
            role=role,  # type: ignore[arg-type]
            session_id=session_id,
            token_version=int(payload.get("token_version", user.token_version)),
        )

    def refresh(self, refresh_token: str) -> TokenPair:
        now = self._now()
        record = self.store.get_refresh(hash_token(refresh_token))
        if record is None:
            raise ApiError(
                code="token_invalid",
                title="Session invalid",
                status=401,
                detail="Sign in again.",
            )
        if record.revoked_at is not None:
            raise ApiError(
                code="token_invalid",
                title="Session invalid",
                status=401,
                detail="The session has ended. Sign in again.",
            )
        if record.used_at is not None:
            self.store.revoke_family(record.family_id, now)
            self._audit(
                "auth.token_reuse_detected",
                entity_type="session",
                entity_id=record.family_id,
                actor_id=record.user_id,
                detail={"action": "family_revoked"},
            )
            raise ApiError(
                code="token_reused",
                title="Session revoked",
                status=401,
                detail="The refresh token was already used. Sign in again.",
            )
        if now >= record.expires_at:
            raise ApiError(
                code="token_expired",
                title="Session expired",
                status=401,
                detail="Sign in again.",
            )
        user = self.store.get_user(record.user_id)
        if user is None or user.status != "active":
            self.store.revoke_family(record.family_id, now)
            raise ApiError(
                code="token_invalid",
                title="Session invalid",
                status=401,
                detail="Sign in again.",
            )
        if record.token_version != user.token_version:
            self.store.revoke_family(record.family_id, now)
            self._audit(
                "auth.token_revoked",
                entity_type="session",
                entity_id=record.family_id,
                actor_id=user.user_id,
                detail={"reason": "token_version_changed"},
            )
            raise ApiError(
                code="token_version_changed",
                title="Session superseded",
                status=401,
                detail="Your roles changed. Sign in again.",
            )
        if record.role not in user.roles:
            self.store.revoke_family(record.family_id, now)
            raise ApiError(
                code="forbidden",
                title="Role no longer assigned",
                status=403,
                detail="Sign in again.",
            )
        record.used_at = now
        self.store.save_refresh(record)
        tokens = self._issue_tokens(
            user,
            record.role,
            family_id=record.family_id,
            device_id=record.device_id,
        )
        self._audit(
            "auth.token_refreshed",
            entity_type="session",
            entity_id=record.family_id,
            actor_id=user.user_id,
            detail={"role": record.role},
        )
        return tokens

    def logout(self, context: AuthContext) -> None:
        now = self._now()
        self.store.revoke_family(context.session_id, now)
        self._audit(
            "auth.logout",
            entity_type="session",
            entity_id=context.session_id,
            actor_id=context.user.user_id,
        )

    def logout_all(self, context: AuthContext) -> None:
        now = self._now()
        revoked = self.store.revoke_all_for_user(context.user.user_id, now)
        self._audit(
            "auth.logout_all",
            entity_type="user",
            entity_id=context.user.user_id,
            actor_id=context.user.user_id,
            detail={"revoked_families": revoked},
        )

    # -- self service --------------------------------------------------

    def profile(self, context: AuthContext) -> UserProfile:
        return self._profile(self._get_user(context.user.user_id))

    def consent_overview(self, user_id: str) -> ConsentOverview:
        records = self.store.consents_for_user(user_id)
        latest: dict[str, ConsentRecord] = {}
        for record in records:
            current = latest.get(record.consent_type)
            if current is None or record.recorded_at >= current.recorded_at:
                latest[record.consent_type] = record
        states: list[ConsentState] = []
        missing: list[ConsentType] = []
        for definition in self._catalog:
            record = latest.get(definition.consent_type)
            needs_reconsent = record is not None and record.version != definition.version
            granted = bool(record and record.granted and not needs_reconsent)
            states.append(
                ConsentState(
                    consent_type=definition.consent_type,
                    required=definition.required,
                    version=definition.version,
                    granted=granted,
                    recorded_at=record.recorded_at if record else None,
                    needs_reconsent=needs_reconsent,
                )
            )
            if definition.required and not granted:
                missing.append(definition.consent_type)
        return ConsentOverview(
            catalog=list(self._catalog),
            states=states,
            missing_required=missing,
            consent_complete=not missing,
        )

    def update_consents(self, context: AuthContext, update: ConsentUpdate) -> ConsentOverview:
        user = self._get_user(context.user.user_id)
        if user.status != "active":
            raise ApiError(
                code="account_disabled",
                title="Account unavailable",
                status=403,
                detail="Consent cannot be changed for this account.",
            )
        seen: set[str] = set()
        now = self._now()
        for decision in update.decisions:
            if decision.consent_type in seen:
                raise ApiError(
                    code="duplicate_consent",
                    title="Duplicate consent",
                    status=422,
                    detail=f"{decision.consent_type} appears more than once.",
                )
            seen.add(decision.consent_type)
            definition = self._catalog_by_type.get(decision.consent_type)
            if definition is None:
                raise ApiError(
                    code="unknown_consent",
                    title="Unknown consent",
                    status=422,
                    detail=f"{decision.consent_type} is not a supported consent.",
                )
            record = ConsentRecord(
                consent_id=_id("cons"),
                user_id=user.user_id,
                consent_type=definition.consent_type,
                version=definition.version,
                granted=decision.granted,
                recorded_at=now,
                channel=update.channel,
                text_hash=definition.text_hash,
            )
            self.store.add_consent(record)
            self._audit(
                "consent.granted" if decision.granted else "consent.withdrawn",
                entity_type="consent",
                entity_id=record.consent_id,
                actor_id=user.user_id,
                detail={
                    "consent_type": definition.consent_type,
                    "version": definition.version,
                    "channel": update.channel,
                },
            )
        return self.consent_overview(user.user_id)

    def assert_required_consents(self, user_id: str) -> ConsentOverview:
        overview = self.consent_overview(user_id)
        if overview.missing_required:
            raise ApiError(
                code="consent_required",
                title="Consent required",
                status=403,
                detail="Accept the required consents before submitting a report.",
                fields=[
                    {"field": consent, "message": "Consent is required."}
                    for consent in overview.missing_required
                ],
            )
        return overview

    def export_user_data(self, context: AuthContext, *, purpose: str) -> ExportBundle:
        user = self._get_user(context.user.user_id)
        if user.status == "deleted":
            raise ApiError(
                code="account_deleted",
                title="Account deleted",
                status=410,
                detail="This account has been deleted.",
            )
        written_purpose = purpose.strip()
        if len(written_purpose) < 8:
            raise ApiError(
                code="purpose_required",
                title="Purpose required",
                status=400,
                detail="Record a written purpose of at least 8 characters for the export.",
            )
        now = self._now()
        self._audit(
            "privacy.export_requested",
            entity_type="user",
            entity_id=user.user_id,
            actor_id=user.user_id,
            detail={"purpose": written_purpose},
        )
        events = [
            event
            for event in self.store.audit.events()
            if event.actor_id == user.user_id or event.entity_id == user.user_id
        ]
        bundle = ExportBundle(
            exported_at=now,
            user=self._profile(user),
            consents=self.store.consents_for_user(user.user_id),
            privacy_requests=self.store.privacy_requests_for_user(user.user_id),
            audit_events=[event.model_dump(mode="json") for event in events],
            notes=[
                "This export contains records for this account only.",
                "Passwords, MFA secrets, OTP codes and session tokens are never included.",
                "Case, image and model-prediction records do not exist in this scaffold.",
            ],
        )
        self._audit(
            "export.generated",
            entity_type="user",
            entity_id=user.user_id,
            actor_id=user.user_id,
            detail={"schema_version": bundle.schema_version, "purpose": written_purpose},
        )
        return bundle

    def list_privacy_requests(self, context: AuthContext) -> list[PrivacyRequest]:
        self._get_user(context.user.user_id)
        return self.store.privacy_requests_for_user(context.user.user_id)

    def record_privacy_request(
        self, context: AuthContext, request: PrivacyRequestCreate
    ) -> PrivacyRequest:
        user = self._get_user(context.user.user_id)
        now = self._now()
        record = PrivacyRequest(
            request_id=_id("privacy"),
            user_id=user.user_id,
            kind=request.kind,
            detail=request.detail,
            status="queued",
            created_at=now,
        )
        self.store.add_privacy_request(record)
        self._audit(
            "privacy.request_recorded",
            entity_type="privacy_request",
            entity_id=record.request_id,
            actor_id=user.user_id,
            detail={"kind": request.kind, "reason": request.reason},
        )
        return record

    def delete_account(
        self,
        context: AuthContext,
        *,
        confirmation: str,
        reason: str,
    ) -> DeletionResult:
        if confirmation != "DELETE":
            raise ApiError(
                code="deletion_confirmation_required",
                title="Confirmation required",
                status=400,
                detail='Send confirmation="DELETE" to delete the account.',
            )
        user = self._get_user(context.user.user_id)
        queued = self._queued_report_count(user.user_id)
        if queued:
            raise ApiError(
                code="queued_reports_exist",
                title="Queued reports must be resolved",
                status=409,
                detail=(
                    f"{queued} queued report(s) remain. Sync or explicitly discard "
                    "them before deleting the account."
                ),
            )
        now = self._now()
        hard_delete_after = (
            now + self._deletion_retention if self._deletion_retention is not None else None
        )
        self.store.revoke_all_for_user(user.user_id, now)
        self._save(
            user,
            status="deleted",
            deleted_at=now,
            hard_delete_after=hard_delete_after,
            token_version=user.token_version + 1,
        )
        self._audit(
            "privacy.deleted",
            entity_type="user",
            entity_id=user.user_id,
            actor_id=user.user_id,
            detail={
                "reason": reason,
                "hard_delete_scheduled": hard_delete_after is not None,
            },
        )
        return DeletionResult(deleted_at=now, hard_delete_after=hard_delete_after)

    # -- admin ---------------------------------------------------------

    def provision_staff(self, actor: AuthContext, request: StaffCreateRequest) -> StaffProvisioned:
        self._require_admin(actor)
        roles = list(dict.fromkeys(request.roles))
        if any(role not in STAFF_ROLES for role in roles):
            raise ApiError(
                code="invalid_role",
                title="Invalid role",
                status=422,
                detail=(
                    "Admin provisioning accepts staff roles only. Farmers self-register with OTP."
                ),
            )
        email = self._normalise_email(request.email)
        if self.store.user_by_email(email) is not None:
            raise ApiError(
                code="email_in_use",
                title="Email already registered",
                status=409,
                detail="Use a different email address.",
            )
        password = request.password.get_secret_value()
        if len(password) < _MIN_PASSWORD_LENGTH:
            raise ApiError(
                code="weak_password",
                title="Password too short",
                status=422,
                detail=f"Use at least {_MIN_PASSWORD_LENGTH} characters.",
            )
        now = self._now()
        needs_mfa = request.require_mfa or any(role in MFA_REQUIRED_ROLES for role in roles)
        secret = generate_totp_secret() if needs_mfa else None
        user = User(
            user_id=_id("usr"),
            kind="staff",
            email=email,
            password_hash=hash_password(password, self._scrypt),
            roles=roles,
            mfa_secret=secret,
            mfa_enabled=secret is not None,
            created_at=now,
            updated_at=now,
        )
        user = self.store.add_user(user)
        self._audit(
            "user.created",
            entity_type="user",
            entity_id=user.user_id,
            actor_id=actor.user.user_id,
            detail={"roles": ",".join(roles), "mfa_required": needs_mfa, "reason": request.reason},
        )
        return StaffProvisioned(
            user=self._summary(user),
            mfa_secret=secret,
            otpauth_uri=otpauth_uri(secret, email) if secret else None,
        )

    def list_users(self, actor: AuthContext) -> list[UserSummary]:
        self._require_admin(actor)
        return [self._summary(user) for user in self.store.list_users()]

    def admin_view_user(self, actor: AuthContext, user_id: str, reason: str) -> AdminUserDetail:
        self._require_admin(actor)
        if len(reason.strip()) < 8:
            raise ApiError(
                code="reason_required",
                title="Reason required",
                status=400,
                detail="Record a reason of at least 8 characters before viewing a user record.",
            )
        user = self._get_user(user_id)
        # The audit event is written before the record is returned.
        self._audit(
            "admin.record_viewed",
            entity_type="user",
            entity_id=user.user_id,
            actor_id=actor.user.user_id,
            detail={"reason": reason.strip(), "view": "user_record"},
        )
        overview = self.consent_overview(user.user_id)
        return AdminUserDetail(
            **self._summary(user).model_dump(),
            last_login_at=user.last_login_at,
            consent_complete=overview.consent_complete,
            active_consents=[
                state.consent_type
                for state in overview.states
                if state.granted and not state.needs_reconsent
            ],
        )

    def change_roles(
        self, actor: AuthContext, user_id: str, request: RoleUpdateRequest
    ) -> UserSummary:
        self._require_admin(actor)
        if user_id == actor.user.user_id:
            raise ApiError(
                code="cannot_change_own_roles",
                title="Cannot change own roles",
                status=409,
                detail="Ask another admin to change your roles.",
            )
        roles = list(dict.fromkeys(request.roles))
        if any(role not in ROLES for role in roles):
            raise ApiError(
                code="invalid_role",
                title="Invalid role",
                status=422,
                detail="Only the five defined roles can be assigned.",
            )
        if any(role not in STAFF_ROLES for role in roles):
            raise ApiError(
                code="invalid_role",
                title="Invalid role",
                status=422,
                detail="Staff accounts hold staff roles only. Farmers self-register with OTP.",
            )
        user = self._get_user(user_id)
        if user.kind != "staff":
            raise ApiError(
                code="invalid_target",
                title="Roles are managed on staff accounts",
                status=409,
                detail="Farmers self-register with OTP and cannot be promoted here.",
            )
        if any(role in MFA_REQUIRED_ROLES for role in roles) and not user.mfa_secret:
            raise ApiError(
                code="mfa_not_provisioned",
                title="MFA not provisioned",
                status=409,
                detail=(
                    "This role requires MFA. Re-provision the account with an MFA "
                    "secret before assigning the role."
                ),
            )
        before = list(user.roles)
        if "admin" in before and "admin" not in roles:
            remaining = [
                candidate
                for candidate in self.store.list_users()
                if candidate.user_id != user.user_id
                and candidate.status == "active"
                and "admin" in candidate.roles
            ]
            if not remaining:
                raise ApiError(
                    code="last_admin",
                    title="Cannot remove the last admin",
                    status=409,
                    detail="Assign another active admin before removing this role.",
                )
        updated = self._save(user, roles=roles, token_version=user.token_version + 1)
        self._audit(
            "user.role_changed",
            entity_type="user",
            entity_id=user.user_id,
            actor_id=actor.user.user_id,
            detail={
                "roles_before": ",".join(before),
                "roles_after": ",".join(roles),
                "reason": request.reason,
                "token_version": updated.token_version,
            },
        )
        return self._summary(updated)

    def set_user_status(
        self, actor: AuthContext, user_id: str, request: UserStatusUpdate
    ) -> UserSummary:
        self._require_admin(actor)
        if user_id == actor.user.user_id:
            raise ApiError(
                code="cannot_change_own_status",
                title="Cannot change own status",
                status=409,
                detail="Ask another admin to disable or re-enable your account.",
            )
        user = self._get_user(user_id)
        if user.kind != "staff":
            raise ApiError(
                code="invalid_target",
                title="Staff accounts only",
                status=409,
                detail="Farmer accounts are disabled through privacy or support procedures.",
            )
        if request.status == "disabled" and "admin" in user.roles:
            remaining = [
                candidate
                for candidate in self.store.list_users()
                if candidate.user_id != user.user_id
                and candidate.status == "active"
                and "admin" in candidate.roles
            ]
            if not remaining:
                raise ApiError(
                    code="last_admin",
                    title="Cannot disable the last admin",
                    status=409,
                    detail="Assign another active admin before disabling this account.",
                )
        now = self._now()
        changes: dict[str, object] = {"status": request.status}
        if request.status == "disabled":
            changes["token_version"] = user.token_version + 1
            self.store.revoke_all_for_user(user.user_id, now)
        updated = self._save(user, **changes)
        self._audit(
            "user.disabled" if request.status == "disabled" else "user.enabled",
            entity_type="user",
            entity_id=user.user_id,
            actor_id=actor.user.user_id,
            detail={"status": request.status, "reason": request.reason.strip()},
        )
        return self._summary(updated)

    def export_aggregates(
        self, actor: AuthContext, request: AdminExportRequest
    ) -> AdminExportSummary:
        self._require_admin(actor)
        users = self.store.list_users()
        if len(users) > request.row_limit:
            raise ApiError(
                code="row_limit_exceeded",
                title="Export exceeds row limit",
                status=413,
                detail=(
                    f"{len(users)} records exceed the {request.row_limit}-row limit. "
                    "Raise the limit deliberately and record the reason."
                ),
            )
        counts_by_role = {role: 0 for role in ROLES}
        counts_by_status = {"active": 0, "disabled": 0, "deleted": 0}
        for user in users:
            for role in user.roles:
                counts_by_role[role] = counts_by_role.get(role, 0) + 1
            counts_by_status[user.status] = counts_by_status.get(user.status, 0) + 1
        now = self._now()
        summary = AdminExportSummary(
            exported_at=now,
            purpose=request.purpose.strip(),
            row_limit=request.row_limit,
            total_users=len(users),
            counts_by_role=counts_by_role,
            counts_by_status=counts_by_status,
        )
        self._audit(
            "export.generated",
            entity_type="system",
            entity_id="admin_export",
            actor_id=actor.user.user_id,
            detail={
                "purpose": summary.purpose,
                "row_limit": summary.row_limit,
                "total_users": summary.total_users,
                "aggregate_only": True,
            },
        )
        return summary

    def run_retention(self, actor: AuthContext, reason: str) -> RetentionResult:
        self._require_admin(actor)
        if len(reason.strip()) < 8:
            raise ApiError(
                code="reason_required",
                title="Reason required",
                status=400,
                detail="Record a reason of at least 8 characters.",
            )
        now = self._now()
        otp_removed = 0
        for challenge in list(self.store.otp_challenges()):
            if challenge.expires_at <= now or challenge.consumed_at is not None:
                self.store.delete_otp(challenge.phone)
                otp_removed += 1
        refresh_removed = 0
        for record in list(self.store.refresh_tokens()):
            if record.expires_at <= now:
                self.store.delete_refresh(record.token_hash)
                refresh_removed += 1
        self.store.prune_otp_request_log(now - self._otp_rate_window)
        self._audit(
            "maintenance.retention_run",
            entity_type="system",
            entity_id="retention",
            actor_id=actor.user.user_id,
            detail={
                "reason": reason.strip(),
                "expired_otp_challenges": otp_removed,
                "expired_refresh_tokens": refresh_removed,
            },
        )
        return RetentionResult(
            expired_otp_challenges=otp_removed,
            expired_refresh_tokens=refresh_removed,
            expired_mfa_challenges=0,
        )

    def bootstrap_admin(self, email: str, password: str, totp_secret: str) -> User | None:
        """Create the first admin from explicit deployment configuration.

        Returns ``None`` when the account already exists. The secret is never
        logged. This is for partner onboarding, not a public endpoint.
        """

        normalised = self._normalise_email(email)
        existing = self.store.user_by_email(normalised)
        if existing is not None:
            return None
        if len(password) < _MIN_PASSWORD_LENGTH:
            raise ApiError(
                code="weak_password",
                title="Password too short",
                status=422,
                detail=f"Use at least {_MIN_PASSWORD_LENGTH} characters.",
            )
        now = self._now()
        user = User(
            user_id=_id("usr"),
            kind="staff",
            email=normalised,
            password_hash=hash_password(password, self._scrypt),
            roles=["admin"],
            mfa_secret=totp_secret,
            mfa_enabled=True,
            created_at=now,
            updated_at=now,
        )
        user = self.store.add_user(user)
        self._audit(
            "user.created",
            entity_type="user",
            entity_id=user.user_id,
            actor_id="bootstrap",
            detail={"roles": "admin", "mfa_required": True, "reason": "deployment bootstrap"},
        )
        return user

    # -- test/debug helpers -------------------------------------------

    def audit_events(self) -> list[AuditEvent]:
        return self.store.audit.events()

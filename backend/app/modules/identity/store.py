"""Process-local identity storage.

The production implementation will be SQLAlchemy tables added by an Alembic
migration. This scaffold keeps the same service contract and is explicitly not
durable: sessions, OTPs and consents are lost on restart.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock

from app.core.audit import AuditLog
from app.modules.identity.models import ConsentRecord, PrivacyRequest, Role, User


@dataclass
class RefreshTokenRecord:
    token_hash: str
    family_id: str
    user_id: str
    token_version: int
    role: Role
    issued_at: datetime
    expires_at: datetime
    used_at: datetime | None = None
    revoked_at: datetime | None = None
    device_id: str | None = None


@dataclass
class OtpChallenge:
    phone: str
    code_hash: str
    created_at: datetime
    expires_at: datetime
    attempts: int = 0
    consumed_at: datetime | None = None


@dataclass
class _Store:
    users: dict[str, User] = field(default_factory=dict)
    phone_index: dict[str, str] = field(default_factory=dict)
    email_index: dict[str, str] = field(default_factory=dict)
    consents: list[ConsentRecord] = field(default_factory=list)
    privacy_requests: list[PrivacyRequest] = field(default_factory=list)
    refresh_tokens: dict[str, RefreshTokenRecord] = field(default_factory=dict)
    otp_challenges: dict[str, OtpChallenge] = field(default_factory=dict)
    otp_request_log: list[tuple[str, datetime]] = field(default_factory=list)
    audit: AuditLog = field(default_factory=AuditLog)


class IdentityStore:
    """Thread-safe in-memory store with no update-in-place of audit rows."""

    def __init__(self) -> None:
        self._data = _Store()
        self._lock = RLock()

    # -- users ---------------------------------------------------------

    def add_user(self, user: User) -> User:
        with self._lock:
            if user.phone:
                existing = self._data.phone_index.get(user.phone)
                if existing is not None and existing != user.user_id:
                    raise ValueError("phone already registered")
                self._data.phone_index[user.phone] = user.user_id
            if user.email:
                email = user.email.lower()
                existing = self._data.email_index.get(email)
                if existing is not None and existing != user.user_id:
                    raise ValueError("email already registered")
                self._data.email_index[email] = user.user_id
            self._data.users[user.user_id] = user
            return user

    def save_user(self, user: User) -> User:
        with self._lock:
            if user.user_id not in self._data.users:
                raise KeyError(user.user_id)
            self._data.users[user.user_id] = user
            if user.phone:
                self._data.phone_index[user.phone] = user.user_id
            if user.email:
                self._data.email_index[user.email.lower()] = user.user_id
            return user

    def get_user(self, user_id: str) -> User | None:
        with self._lock:
            return self._data.users.get(user_id)

    def user_by_phone(self, phone: str) -> User | None:
        with self._lock:
            user_id = self._data.phone_index.get(phone)
            return self._data.users.get(user_id) if user_id else None

    def user_by_email(self, email: str) -> User | None:
        with self._lock:
            user_id = self._data.email_index.get(email.lower())
            return self._data.users.get(user_id) if user_id else None

    def list_users(self) -> list[User]:
        with self._lock:
            return list(self._data.users.values())

    # -- consent -------------------------------------------------------

    def add_consent(self, record: ConsentRecord) -> ConsentRecord:
        with self._lock:
            self._data.consents.append(record)
            return record

    def consents_for_user(self, user_id: str) -> list[ConsentRecord]:
        with self._lock:
            return [item for item in self._data.consents if item.user_id == user_id]

    # -- sessions ------------------------------------------------------

    def add_refresh(self, record: RefreshTokenRecord) -> RefreshTokenRecord:
        with self._lock:
            self._data.refresh_tokens[record.token_hash] = record
            return record

    def get_refresh(self, token_hash: str) -> RefreshTokenRecord | None:
        with self._lock:
            return self._data.refresh_tokens.get(token_hash)

    def save_refresh(self, record: RefreshTokenRecord) -> RefreshTokenRecord:
        with self._lock:
            self._data.refresh_tokens[record.token_hash] = record
            return record

    def delete_refresh(self, token_hash: str) -> None:
        with self._lock:
            self._data.refresh_tokens.pop(token_hash, None)

    def family_tokens(self, family_id: str) -> list[RefreshTokenRecord]:
        with self._lock:
            return [
                record
                for record in self._data.refresh_tokens.values()
                if record.family_id == family_id
            ]

    def revoke_family(self, family_id: str, at: datetime) -> int:
        with self._lock:
            revoked = 0
            for record in self._data.refresh_tokens.values():
                if record.family_id == family_id and record.revoked_at is None:
                    record.revoked_at = at
                    revoked += 1
            return revoked

    def revoke_all_for_user(self, user_id: str, at: datetime) -> int:
        with self._lock:
            revoked = 0
            for record in self._data.refresh_tokens.values():
                if record.user_id == user_id and record.revoked_at is None:
                    record.revoked_at = at
                    revoked += 1
            return revoked

    def refresh_tokens(self) -> list[RefreshTokenRecord]:
        with self._lock:
            return list(self._data.refresh_tokens.values())

    # -- one-time codes ------------------------------------------------

    def put_otp(self, challenge: OtpChallenge) -> OtpChallenge:
        with self._lock:
            self._data.otp_challenges[challenge.phone] = challenge
            return challenge

    def get_otp(self, phone: str) -> OtpChallenge | None:
        with self._lock:
            return self._data.otp_challenges.get(phone)

    def save_otp(self, challenge: OtpChallenge) -> OtpChallenge:
        with self._lock:
            self._data.otp_challenges[challenge.phone] = challenge
            return challenge

    def delete_otp(self, phone: str) -> None:
        with self._lock:
            self._data.otp_challenges.pop(phone, None)

    def otp_challenges(self) -> list[OtpChallenge]:
        with self._lock:
            return list(self._data.otp_challenges.values())

    # -- rate limiting -------------------------------------------------

    def record_otp_request(self, key: str, at: datetime) -> None:
        with self._lock:
            self._data.otp_request_log.append((key, at))

    def count_otp_requests(self, key: str, since: datetime) -> int:
        with self._lock:
            return sum(
                1
                for logged_key, at in self._data.otp_request_log
                if logged_key == key and at >= since
            )

    def prune_otp_request_log(self, before: datetime) -> int:
        with self._lock:
            kept = [item for item in self._data.otp_request_log if item[1] >= before]
            removed = len(self._data.otp_request_log) - len(kept)
            self._data.otp_request_log = kept
            return removed

    # -- privacy requests ---------------------------------------------

    def add_privacy_request(self, request: PrivacyRequest) -> PrivacyRequest:
        with self._lock:
            self._data.privacy_requests.append(request)
            return request

    def privacy_requests_for_user(self, user_id: str) -> list[PrivacyRequest]:
        with self._lock:
            return [item for item in self._data.privacy_requests if item.user_id == user_id]

    # -- audit ---------------------------------------------------------

    @property
    def audit(self) -> AuditLog:
        return self._data.audit

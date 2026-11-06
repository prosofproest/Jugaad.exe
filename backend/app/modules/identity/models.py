"""Identity, role, consent and privacy models (spec 03).

Only five roles exist. Anything else is rejected at the boundary rather than
silently ignored, so a typo can never grant a broader capability.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr

Role = Literal["farmer", "extension_worker", "pathologist", "agronomist", "admin"]

ROLES: tuple[Role, ...] = (
    "farmer",
    "extension_worker",
    "pathologist",
    "agronomist",
    "admin",
)

STAFF_ROLES: tuple[Role, ...] = ("extension_worker", "pathologist", "agronomist", "admin")

# Spec 03 §4.2: MFA is mandatory for these roles. extension_worker is
# "strongly recommended" only, so it is opt-in per account.
MFA_REQUIRED_ROLES: frozenset[Role] = frozenset({"pathologist", "agronomist", "admin"})

ConsentType = Literal[
    "service_privacy",
    "image_assessment",
    "approximate_location",
    "research_model_improvement",
    "extension_worker_contact",
]

UserStatus = Literal["active", "disabled", "deleted"]


class User(BaseModel):
    """Internal user record. Never returned directly by an endpoint."""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    kind: Literal["farmer", "staff"]
    phone: str | None = None
    email: str | None = None
    password_hash: str | None = None
    roles: list[Role] = Field(default_factory=list)
    mfa_secret: str | None = None
    mfa_enabled: bool = False
    status: UserStatus = "active"
    token_version: int = 1
    failed_login_at: list[datetime] = Field(default_factory=list)
    locked_until: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    hard_delete_after: datetime | None = None


class UserSummary(BaseModel):
    """Role-safe projection used by list/detail endpoints."""

    user_id: str
    kind: Literal["farmer", "staff"]
    roles: list[Role]
    status: UserStatus
    email: str | None = None
    phone_masked: str | None = None
    mfa_enabled: bool
    created_at: datetime
    updated_at: datetime


class UserProfile(UserSummary):
    """The caller's own profile. Includes their own contact data."""

    phone: str | None = None
    last_login_at: datetime | None = None


class ConsentDefinition(BaseModel):
    """Versioned plain-language consent text.

    ``text_hash`` is computed from the version and the exact text so a later
    wording change is detectable without storing the whole text per record.
    """

    consent_type: ConsentType
    required: bool
    version: str
    title: str
    summary: str
    text_hash: str


class ConsentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consent_id: str
    user_id: str
    consent_type: ConsentType
    version: str
    granted: bool
    recorded_at: datetime
    channel: str
    text_hash: str


class ConsentState(BaseModel):
    consent_type: ConsentType
    required: bool
    version: str
    granted: bool
    recorded_at: datetime | None = None
    needs_reconsent: bool = False


class ConsentOverview(BaseModel):
    catalog: list[ConsentDefinition]
    states: list[ConsentState]
    missing_required: list[ConsentType]
    consent_complete: bool


class ConsentDecision(BaseModel):
    consent_type: ConsentType
    granted: bool


class ConsentUpdate(BaseModel):
    decisions: list[ConsentDecision] = Field(min_length=1, max_length=5)
    channel: str = Field(default="api", max_length=40)


class OtpRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)


class OtpVerifyRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    code: str = Field(min_length=6, max_length=6)
    device_id: str | None = Field(default=None, max_length=128)


class OtpRequested(BaseModel):
    status: Literal["accepted"] = "accepted"
    message: str = (
        "If this number can be used, a code was sent. The response is the same "
        "whether or not an account already exists."
    )


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: SecretStr
    role: Role | None = None


class MfaVerifyRequest(BaseModel):
    challenge: str = Field(min_length=10, max_length=4096)
    totp: str = Field(min_length=6, max_length=6)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=200)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    refresh_expires_in: int
    user_id: str
    role: Role


class LoginResponse(BaseModel):
    mfa_required: bool
    challenge_token: str | None = None
    challenge_expires_in: int | None = None
    tokens: TokenPair | None = None


class StaffCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: SecretStr
    roles: list[Role] = Field(min_length=1, max_length=5)
    require_mfa: bool = True
    reason: str = Field(min_length=8, max_length=500)


class StaffProvisioned(BaseModel):
    user: UserSummary
    mfa_secret: str | None = None
    otpauth_uri: str | None = None
    note: str = (
        "The MFA secret is shown once. Store it in the authenticator before "
        "closing this response; it is not retrievable later."
    )


class RoleUpdateRequest(BaseModel):
    roles: list[Role] = Field(min_length=1, max_length=5)
    reason: str = Field(min_length=8, max_length=500)


class UserStatusUpdate(BaseModel):
    status: Literal["active", "disabled"]
    reason: str = Field(min_length=8, max_length=500)


class MaintenanceRequest(BaseModel):
    reason: str = Field(min_length=8, max_length=500)


class AdminExportRequest(BaseModel):
    purpose: str = Field(min_length=8, max_length=500)
    row_limit: int = Field(default=1000, ge=1, le=10_000)


class AdminExportSummary(BaseModel):
    """Aggregate-only export. Contains no names, emails, phones or case rows."""

    schema_version: Literal["1.0"] = "1.0"
    exported_at: datetime
    purpose: str
    row_limit: int
    total_users: int
    counts_by_role: dict[str, int]
    counts_by_status: dict[str, int]
    note: str = (
        "Aggregate identity counts only. No phone numbers, email addresses, "
        "case data or free-text records are included."
    )


class AdminUserDetail(UserSummary):
    last_login_at: datetime | None = None
    consent_complete: bool | None = None
    active_consents: list[ConsentType] = Field(default_factory=list)


class DeletionRequest(BaseModel):
    confirmation: str = Field(min_length=6, max_length=6)
    reason: str = Field(default="user requested account deletion", max_length=500)


class DeletionResult(BaseModel):
    status: Literal["scheduled"] = "scheduled"
    deleted_at: datetime
    hard_delete_after: datetime | None
    hard_delete_policy: str = (
        "No hard-delete date is set until decision D10 fixes the retention "
        "policy. The account is soft-deleted and its sessions are revoked now."
    )


PrivacyRequestKind = Literal["access", "correction", "objection", "deletion"]

PrivacyRequestStatus = Literal["queued", "completed", "rejected"]


class PrivacyRequestCreate(BaseModel):
    kind: PrivacyRequestKind
    detail: str = Field(min_length=8, max_length=1000)
    reason: str = Field(default="user requested", max_length=500)


class PrivacyRequest(BaseModel):
    request_id: str
    user_id: str
    kind: PrivacyRequestKind
    detail: str
    status: PrivacyRequestStatus
    created_at: datetime


class RetentionResult(BaseModel):
    expired_otp_challenges: int
    expired_refresh_tokens: int
    expired_mfa_challenges: int
    note: str = (
        "Only short-lived credentials are purged. Case, image and audit "
        "retention stays unset until decision D10 is closed."
    )


class ExportBundle(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    exported_at: datetime
    user: UserProfile
    consents: list[ConsentRecord]
    privacy_requests: list[PrivacyRequest]
    audit_events: list[dict[str, Any]]
    notes: list[str] = Field(default_factory=list)

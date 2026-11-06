"""Advisory content model (spec 07 §2).

Advisory text is curated and approved, never generated. This module only
describes the data; the validator in ``validator.py`` decides whether the text
may be published.
"""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

QualifiedRole = Literal["agronomist", "pathologist"]
QUALIFIED_ROLES: frozenset[str] = frozenset({"agronomist", "pathologist"})

ActionType = Literal[
    "scout",
    "monitor",
    "sanitise",
    "crop_management",
    "escalate",
    "record",
]
ACTION_TYPES: frozenset[str] = frozenset(
    {"scout", "monitor", "sanitise", "crop_management", "escalate", "record"}
)

AdvisoryStatus = Literal["draft", "approved", "published", "withdrawn"]

ALL_SUPPORTED_AREAS = "all_supported_areas"


class AdvisoryBody(BaseModel):
    """The six required body sections from spec 07 §2."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    what_this_is_about: str = Field(min_length=1, max_length=8000)
    what_you_may_see: str = Field(min_length=1, max_length=8000)
    what_to_do_now: str = Field(min_length=1, max_length=8000)
    what_not_to_assume: str = Field(min_length=1, max_length=8000)
    when_to_escalate: str = Field(min_length=1, max_length=8000)
    source_and_approval: str = Field(min_length=1, max_length=8000)


class AdvisoryDraft(BaseModel):
    """Input for a new advisory version.

    ``author_role`` is supplied explicitly because identity and role storage is
    not implemented yet. The value is still checked against the qualified role
    set, so a caller cannot label an unqualified author as qualified by leaving
    the field out.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    crop_code: str = Field(min_length=1, max_length=80)
    target_code: str = Field(min_length=1, max_length=80)
    geo_scope: list[str] = Field(min_length=1, max_length=200)
    language: str = Field(min_length=2, max_length=16)
    title: str = Field(min_length=1, max_length=200)
    body: AdvisoryBody
    action_types: list[ActionType] = Field(min_length=1, max_length=6)
    source: str = Field(min_length=1, max_length=500)
    valid_from: AwareDatetime
    valid_to: AwareDatetime
    author_id: str = Field(min_length=1, max_length=120)
    author_role: QualifiedRole

    @model_validator(mode="after")
    def _consistent(self) -> AdvisoryDraft:
        if self.valid_to <= self.valid_from:
            raise ValueError("valid_to must be after valid_from")
        if len(set(self.geo_scope)) != len(self.geo_scope):
            raise ValueError("geo_scope must be unique")
        if len(set(self.action_types)) != len(self.action_types):
            raise ValueError("action_types must be unique")
        return self


class AdvisoryVersion(BaseModel):
    """An immutable advisory version. Editing always creates a new version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    advisory_id: str
    version: int = Field(ge=1)
    crop_code: str
    target_code: str
    geo_scope: tuple[str, ...]
    language: str
    title: str
    body: AdvisoryBody
    action_types: tuple[ActionType, ...]
    source: str
    valid_from: AwareDatetime
    valid_to: AwareDatetime
    author_id: str
    author_role: QualifiedRole
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    created_at: AwareDatetime


class AdvisoryApproval(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    advisory_id: str
    version: int
    approver_id: str
    approver_role: QualifiedRole
    approved_at: AwareDatetime
    notes: str | None = None


class Advisory(BaseModel):
    """Logical advisory plus its retained version history."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    advisory_id: str
    status: AdvisoryStatus
    current_version: int
    versions: tuple[AdvisoryVersion, ...]
    approvals: tuple[AdvisoryApproval, ...]
    withdrawn_reason: str | None
    created_at: AwareDatetime
    published_at: AwareDatetime | None

    def version(self, number: int) -> AdvisoryVersion:
        for item in self.versions:
            if item.version == number:
                return item
        raise KeyError(number)

    def approval_for(self, number: int) -> AdvisoryApproval | None:
        for item in self.approvals:
            if item.version == number:
                return item
        return None


class ApprovedAdvisoryView(BaseModel):
    """Safe, public projection of an approved and currently valid advisory.

    Internal identifiers of authors and approvers are deliberately omitted.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    advisory_id: str
    version: int
    crop_code: str
    target_code: str
    geo_scope: tuple[str, ...]
    language: str
    title: str
    body: AdvisoryBody
    action_types: tuple[ActionType, ...]
    source: str
    valid_from: AwareDatetime
    valid_to: AwareDatetime
    content_hash: str
    approver_role: QualifiedRole
    approved_at: AwareDatetime


class AdvisoryFallback(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    message: str
    next_step: str


class AdvisoryQueryResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    items: tuple[ApprovedAdvisoryView, ...]
    fallback: AdvisoryFallback | None


def compute_content_hash(
    *,
    crop_code: str,
    target_code: str,
    geo_scope: list[str] | tuple[str, ...],
    language: str,
    title: str,
    body: AdvisoryBody,
    action_types: list[str] | tuple[str, ...],
    source: str,
    valid_from: AwareDatetime,
    valid_to: AwareDatetime,
) -> str:
    """Canonical hash used to detect an unauthorised edit of a version."""

    payload = {
        "crop_code": crop_code,
        "target_code": target_code,
        "geo_scope": sorted(geo_scope),
        "language": language,
        "title": title,
        "body": body.model_dump(),
        "action_types": sorted(action_types),
        "source": source,
        "valid_from": valid_from.isoformat(),
        "valid_to": valid_to.isoformat(),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

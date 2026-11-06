"""Advisory approval workflow and retrieval (spec 07 §3–§4).

Publication rules are enforced here, not in a UI:

- the approver must be a different person from the author;
- the approver must hold ``agronomist`` or ``pathologist``;
- at least two qualified accounts must exist in the supplied roster (D3);
- every edit creates a new immutable version and clears approval;
- expiry is mandatory and expired content is never served;
- withdrawal immediately removes every version from retrieval.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4

from app.core.audit import AuditEvent, AuditLog
from app.modules.advisories.models import (
    ALL_SUPPORTED_AREAS,
    QUALIFIED_ROLES,
    Advisory,
    AdvisoryApproval,
    AdvisoryDraft,
    AdvisoryFallback,
    AdvisoryQueryResult,
    AdvisoryVersion,
    ApprovedAdvisoryView,
    compute_content_hash,
)
from app.modules.advisories.validator import require_valid_advisory

Clock = Callable[[], datetime]


class AdvisoryWorkflowError(ValueError):
    """A typed workflow failure carrying a machine-readable code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass
class _Record:
    advisory_id: str
    versions: list[AdvisoryVersion] = field(default_factory=list)
    approvals: dict[int, AdvisoryApproval] = field(default_factory=dict)
    status: str = "draft"
    current_version: int = 1
    withdrawn_reason: str | None = None
    created_at: datetime | None = None
    published_at: datetime | None = None

    def version(self, number: int) -> AdvisoryVersion:
        for item in self.versions:
            if item.version == number:
                return item
        raise AdvisoryWorkflowError("version_not_found")


class AdvisoryRegistry:
    """In-memory registry with the same contracts the database will enforce."""

    def __init__(self, *, clock: Clock | None = None) -> None:
        self._clock = clock if clock is not None else (lambda: datetime.now(UTC))
        self._records: dict[str, _Record] = {}
        self._audit = AuditLog(self._clock)
        self._lock = RLock()

    # ---------------------------------------------------------------- writes

    def create_draft(self, draft: AdvisoryDraft) -> Advisory:
        require_valid_advisory(draft)
        now = self._clock()
        advisory_id = f"adv_{uuid4().hex}"
        version = self._version_from_draft(advisory_id, 1, draft, now)
        record = _Record(
            advisory_id=advisory_id,
            versions=[version],
            created_at=now,
        )
        with self._lock:
            self._records[advisory_id] = record
        self._audit.record(
            "advisory.draft_created",
            entity_type="advisory",
            entity_id=advisory_id,
            actor_id=draft.author_id,
            detail={"version": 1, "crop": draft.crop_code, "target": draft.target_code},
        )
        return self._public(record)

    def create_version(
        self,
        advisory_id: str,
        draft: AdvisoryDraft,
        *,
        editor_id: str,
    ) -> Advisory:
        """Append a new immutable version and return the advisory to draft."""

        require_valid_advisory(draft)
        with self._lock:
            record = self._require(advisory_id)
            if record.status == "withdrawn":
                raise AdvisoryWorkflowError("advisory_withdrawn")
            number = len(record.versions) + 1
            version = self._version_from_draft(advisory_id, number, draft, self._clock())
            record.versions.append(version)
            record.current_version = number
            record.status = "draft"
            record.published_at = None
        self._audit.record(
            "advisory.version_created",
            entity_type="advisory",
            entity_id=advisory_id,
            actor_id=editor_id,
            detail={"version": number},
        )
        return self._public(record)

    def approve(
        self,
        advisory_id: str,
        *,
        version: int,
        approver_id: str,
        approver_role: str,
        qualified_accounts: Mapping[str, str],
        notes: str | None = None,
    ) -> Advisory:
        """Record a second-person approval.

        ``qualified_accounts`` is the current roster of accounts that hold a
        qualified role. A caller cannot approve by asserting a role alone.
        """

        if approver_role not in QUALIFIED_ROLES:
            raise AdvisoryWorkflowError("approver_not_qualified")
        qualified = {
            account_id
            for account_id, role in qualified_accounts.items()
            if role in QUALIFIED_ROLES
        }
        if len(qualified) < 2:
            raise AdvisoryWorkflowError("insufficient_qualified_accounts")
        if approver_id not in qualified:
            raise AdvisoryWorkflowError("approver_not_in_roster")
        if qualified_accounts.get(approver_id) != approver_role:
            raise AdvisoryWorkflowError("approver_role_mismatch")

        with self._lock:
            record = self._require(advisory_id)
            if record.status == "withdrawn":
                raise AdvisoryWorkflowError("advisory_withdrawn")
            if version != record.current_version:
                raise AdvisoryWorkflowError("stale_version")
            item = record.version(version)
            if item.author_id == approver_id:
                raise AdvisoryWorkflowError("author_cannot_approve")
            if version in record.approvals:
                raise AdvisoryWorkflowError("already_approved")
            approval = AdvisoryApproval(
                advisory_id=advisory_id,
                version=version,
                approver_id=approver_id,
                approver_role=approver_role,  # type: ignore[arg-type]
                approved_at=self._clock(),
                notes=notes,
            )
            record.approvals[version] = approval
            record.status = "approved"
        self._audit.record(
            "advisory.approved",
            entity_type="advisory",
            entity_id=advisory_id,
            actor_id=approver_id,
            detail={"version": version, "role": approver_role},
        )
        return self._public(record)

    def publish(self, advisory_id: str, *, version: int, actor_id: str) -> Advisory:
        with self._lock:
            record = self._require(advisory_id)
            if record.status == "withdrawn":
                raise AdvisoryWorkflowError("advisory_withdrawn")
            if version != record.current_version:
                raise AdvisoryWorkflowError("stale_version")
            if record.status == "published" and record.published_at is not None:
                return self._public(record)
            if record.status != "approved" or version not in record.approvals:
                raise AdvisoryWorkflowError("approval_required")
            item = record.version(version)
            now = self._clock()
            if now >= item.valid_to:
                raise AdvisoryWorkflowError("advisory_expired")
            record.status = "published"
            record.published_at = now
        self._audit.record(
            "advisory.published",
            entity_type="advisory",
            entity_id=advisory_id,
            actor_id=actor_id,
            detail={"version": version, "valid_to": record.version(version).valid_to.isoformat()},
        )
        return self._public(record)

    def withdraw(self, advisory_id: str, *, actor_id: str, reason: str) -> Advisory:
        if not reason.strip():
            raise AdvisoryWorkflowError("withdrawal_reason_required")
        with self._lock:
            record = self._require(advisory_id)
            if record.status == "withdrawn":
                return self._public(record)
            record.status = "withdrawn"
            record.withdrawn_reason = reason.strip()
        self._audit.record(
            "advisory.withdrawn",
            entity_type="advisory",
            entity_id=advisory_id,
            actor_id=actor_id,
            detail={"reason": reason.strip()},
        )
        return self._public(record)

    # ---------------------------------------------------------------- reads

    def get(self, advisory_id: str) -> Advisory | None:
        with self._lock:
            record = self._records.get(advisory_id)
            return self._public(record) if record is not None else None

    def list_all(self) -> tuple[Advisory, ...]:
        with self._lock:
            return tuple(self._public(record) for record in self._records.values())

    def retrieve(
        self,
        *,
        crop: str,
        target: str,
        geo: str,
        language: str,
        now: datetime | None = None,
    ) -> AdvisoryQueryResult:
        """Return only approved, currently valid, in-scope content."""

        at = now if now is not None else self._clock()
        items: list[ApprovedAdvisoryView] = []
        with self._lock:
            for record in self._records.values():
                if record.status != "published":
                    continue
                approval = record.approvals.get(record.current_version)
                if approval is None:
                    continue
                item = record.version(record.current_version)
                if item.crop_code != crop or item.target_code != target:
                    continue
                if item.language != language:
                    continue
                if ALL_SUPPORTED_AREAS not in item.geo_scope and geo not in item.geo_scope:
                    continue
                if not (item.valid_from <= at < item.valid_to):
                    continue
                items.append(
                    ApprovedAdvisoryView(
                        advisory_id=item.advisory_id,
                        version=item.version,
                        crop_code=item.crop_code,
                        target_code=item.target_code,
                        geo_scope=item.geo_scope,
                        language=item.language,
                        title=item.title,
                        body=item.body,
                        action_types=item.action_types,
                        source=item.source,
                        valid_from=item.valid_from,
                        valid_to=item.valid_to,
                        content_hash=item.content_hash,
                        approver_role=approval.approver_role,
                        approved_at=approval.approved_at,
                    )
                )

        items.sort(key=lambda item: (item.title, item.advisory_id))
        fallback = None
        if not items:
            fallback = AdvisoryFallback(
                message="No approved advisory is available for this crop and area yet.",
                next_step="request_expert_review",
            )
        return AdvisoryQueryResult(items=tuple(items), fallback=fallback)

    def audit_events(self) -> list[AuditEvent]:
        return self._audit.events()

    # ------------------------------------------------------------- internals

    def _require(self, advisory_id: str) -> _Record:
        record = self._records.get(advisory_id)
        if record is None:
            raise AdvisoryWorkflowError("advisory_not_found")
        return record

    def _version_from_draft(
        self,
        advisory_id: str,
        number: int,
        draft: AdvisoryDraft,
        now: datetime,
    ) -> AdvisoryVersion:
        content_hash = compute_content_hash(
            crop_code=draft.crop_code,
            target_code=draft.target_code,
            geo_scope=draft.geo_scope,
            language=draft.language,
            title=draft.title,
            body=draft.body,
            action_types=draft.action_types,
            source=draft.source,
            valid_from=draft.valid_from,
            valid_to=draft.valid_to,
        )
        return AdvisoryVersion(
            advisory_id=advisory_id,
            version=number,
            crop_code=draft.crop_code,
            target_code=draft.target_code,
            geo_scope=tuple(draft.geo_scope),
            language=draft.language,
            title=draft.title,
            body=draft.body,
            action_types=tuple(draft.action_types),
            source=draft.source,
            valid_from=draft.valid_from,
            valid_to=draft.valid_to,
            author_id=draft.author_id,
            author_role=draft.author_role,
            content_hash=content_hash,
            created_at=now,
        )

    def _public(self, record: _Record) -> Advisory:
        return Advisory(
            advisory_id=record.advisory_id,
            status=record.status,  # type: ignore[arg-type]
            current_version=record.current_version,
            versions=tuple(record.versions),
            approvals=tuple(record.approvals.values()),
            withdrawn_reason=record.withdrawn_reason,
            created_at=record.created_at or self._clock(),
            published_at=record.published_at,
        )

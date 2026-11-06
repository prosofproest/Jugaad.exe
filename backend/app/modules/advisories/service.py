"""Curated, expert-approved advisory content.

No part of this module generates advisory text. Every version is authored by a
named user, validated against the prohibited-content rules, approved by a second
holder of ``can_approve_advisory`` and served only while valid. A missing
advisory returns an explicit fallback and escalation, never substitute text.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.db.models import (
    Advisory,
    AdvisoryApproval,
    AdvisoryVersion,
    Crop,
    Geography,
    Target,
    User,
)
from app.modules.audit.service import record_audit
from app.modules.identity import service as identity_service

ALLOWED_ACTION_TYPES = {
    "scout",
    "monitor",
    "sanitise",
    "crop_management",
    "escalate",
    "record",
}
ALLOWED_LANGUAGES = {"en", "kn"}
ALL_SUPPORTED_AREAS = "ALL_SUPPORTED_AREAS"

# Each tuple is (violation class, compiled pattern). The validator is code, not
# a style guide; a match rejects publication until the text is reworded.
_PROHIBITED: list[tuple[str, re.Pattern[str]]] = [
    (
        "product_name",
        re.compile(
            r"\b("
            r"carbendazim|mancozeb|chlorothalonil|copper[ _-]?oxychloride|"
            r"copper[ _-]?hydroxide|metalaxyl|cymoxanil|azoxystrobin|"
            r"difenoconazole|propiconazole|tebuconazole|hexaconazole|"
            r"imidacloprid|thiamethoxam|acetamiprid|fipronil|dimethoate|"
            r"monocrotophos|chlorpyrifos|cypermethrin|lambda[ _-]?cyhalothrin|"
            r"glyphosate|paraquat|atrazine|fungicide|insecticide|pesticide|"
            r"herbicide|miticide|nematicide|bactericide|weedicide|"
            r"plant[ _-]?protection[ _-]?product|crop[ _-]?protection[ _-]?chemical"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "dose_or_concentration",
        re.compile(
            r"(\b\d+(?:[.,]\d+)?\s*(?:ml|millilit(?:re|er)s?|l|lit(?:re|er)s?|"
            r"g|gm|grams?|kg|kilograms?)\b\s*(?:/|per|each|every)\s*"
            r"(?:l|lit(?:re|er)|acre|hectare|ha|plant|tree|100\s*l)\b)"
            r"|(\b\d+(?:[.,]\d+)?\s*(?:ml|g|gm|kg)\s*/\s*(?:l|lit(?:re|er)|acre|ha)\b)"
            r"|(\b(?:ml|g|gm|kg)\s*(?:/|per)\s*(?:l|lit(?:re|er)|acre|ha)\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "mixture_instruction",
        re.compile(
            r"\b(?:tank[ _-]?mix|mix(?:ed|ing)?\s+(?:it\s+)?with|"
            r"combine\s+(?:it\s+)?with|add\s+\d|add\s+it\s+to)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "application_interval",
        re.compile(
            r"\b(?:spray|apply|repeat|re-?apply|reapply|again)\b.{0,40}"
            r"\b(?:every|after|at)\s+\d+\s*(?:day|week|hour)s?\b"
            r"|\b\d+\s*(?:day|week)\s*(?:interval|schedule|spacing)s?\b"
            r"|\b(?:every|each)\s+\d+\s*(?:day|week)s?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "pre_harvest_interval",
        re.compile(
            r"\b(?:pre[ _-]?harvest\s+interval|phi)\b"
            r"|\b\d+\s*days?\s*before\s*(?:harvest|picking)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "legal_use_claim",
        re.compile(
            r"\b(?:approved|registered|licensed|legal|permitted)\s+"
            r"(?:for\s+)?(?:use|application)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "guarantee",
        re.compile(
            r"\bguarantee(?:d|s)?\b|\b100\s*%\s*(?:effective|control|safe)\b"
            r"|\bwill\s+(?:definitely\s+)?(?:prevent|eliminate|eradicate|cure)\b"
            r"|\balways\s+(?:works|prevents|controls)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "diagnosis_claim",
        re.compile(
            r"\b(?:this|it|we)\s+(?:confirms?|proves?|diagnoses?)\b"
            r"|\bconfirmed\s+diagnosis\b|\bdiagnosis\s*:\s*\w+"
            r"|\byou\s+have\s+(?:late|early)?\s*blight\b",
            re.IGNORECASE,
        ),
    ),
    (
        "outbreak_claim",
        re.compile(
            r"\b(?:outbreak|epidemic)\s+(?:is\s+)?confirmed\b"
            r"|\bconfirmed\s+(?:outbreak|epidemic)\b"
            r"|\boutbreak\s+in\s+your\s+(?:field|area)\b",
            re.IGNORECASE,
        ),
    ),
]

_REQUIRED_DISCLAIMER = re.compile(
    r"\b(not\s+a\s+diagnosis|not\s+confirmation|early\s+warning|"
    r"not\s+confirmed|assistive)\b",
    re.IGNORECASE,
)


def _now() -> datetime:
    return datetime.now(UTC)


def find_violations(text: str) -> list[dict[str, str]]:
    """Return every prohibited match with its class and snippet."""

    violations: list[dict[str, str]] = []
    for kind, pattern in _PROHIBITED:
        for match in pattern.finditer(text or ""):
            violations.append(
                {
                    "class": kind,
                    "match": match.group(0)[:120],
                    "position": str(match.start()),
                }
            )
    return violations


def validate_content(text: str) -> None:
    violations = find_violations(text)
    if violations:
        raise ApiError(
            422,
            "prohibited_advisory_content",
            "Advisory contains prohibited content",
            detail=(
                "Advisory text may not contain product names, doses, mixtures, "
                "application intervals, legal-use claims, guarantees, diagnosis "
                "claims or outbreak claims."
            ),
            fields=[
                {
                    "field": "body_md",
                    "message": f"{item['class']}: {item['match']}",
                    "type": "prohibited_content",
                }
                for item in violations[:10]
            ],
        )


def _content_hash(*, crop_code: str, target_code: str, language: str, body: str) -> str:
    payload = "\x1f".join([crop_code, target_code, language, body])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_target(db: Session, crop_code: str, target_code: str) -> None:
    crop = db.get(Crop, crop_code)
    if crop is None or not crop.supported:
        raise ApiError(422, "unsupported_crop", "Crop is not on the validated allowlist")
    target = db.scalar(
        select(Target).where(Target.crop_code == crop_code, Target.code == target_code)
    )
    if target is None or not target.supported:
        raise ApiError(422, "unsupported_target", "Target is not on the validated allowlist")


def _validate_scope(db: Session, geo_scope: list[str]) -> list[str]:
    if not geo_scope:
        return [ALL_SUPPORTED_AREAS]
    if ALL_SUPPORTED_AREAS in geo_scope:
        return [ALL_SUPPORTED_AREAS]
    for code in geo_scope:
        if db.scalar(select(Geography).where(Geography.code == code)) is None:
            raise ApiError(422, "unknown_area", f"Unknown area code: {code}")
    return geo_scope


def _validate_common(
    *,
    language: str,
    action_types: list[str],
    valid_from: datetime,
    valid_to: datetime,
    title: str,
    body: str,
) -> None:
    if language not in ALLOWED_LANGUAGES:
        raise ApiError(422, "unsupported_language", "Advisory language must be en or kn")
    unknown = sorted(set(action_types) - ALLOWED_ACTION_TYPES)
    if unknown:
        raise ApiError(
            422,
            "invalid_action_type",
            "Advisory contains an action type outside the approved list",
            detail=f"Unknown action types: {', '.join(unknown)}",
        )
    if not action_types:
        raise ApiError(422, "action_type_required", "At least one action type is required")
    if valid_to <= valid_from:
        raise ApiError(422, "invalid_validity", "valid_to must be after valid_from")
    if not title.strip():
        raise ApiError(422, "title_required", "Advisory title is required")
    if not body.strip():
        raise ApiError(422, "body_required", "Advisory body is required")
    validate_content(f"{title}\n{body}")


def _validate_override(
    db: Session,
    user: User,
    *,
    override_reason: str | None,
) -> None:
    """The only path past a validator false positive. Requires an approver."""

    if not override_reason or len(override_reason.strip()) < 10:
        raise ApiError(
            422,
            "override_reason_required",
            "A written reason is required to override the content validator",
        )
    if "can_approve_advisory" not in identity_service.active_permissions(db, user.id):
        raise ApiError(
            403,
            "forbidden",
            "The can_approve_advisory permission is required to override the validator",
        )


def create_advisory(
    db: Session,
    *,
    user: User,
    crop_code: str,
    target_code: str,
    geo_scope: list[str],
    language: str,
    title: str,
    body_md: str,
    action_types: list[str],
    source: str,
    season: str | None,
    valid_from: datetime,
    valid_to: datetime,
    validator_override_reason: str | None,
) -> Advisory:
    _validate_target(db, crop_code, target_code)
    scope = _validate_scope(db, geo_scope)
    try:
        _validate_common(
            language=language,
            action_types=action_types,
            valid_from=valid_from,
            valid_to=valid_to,
            title=title,
            body=body_md,
        )
    except ApiError as error:
        if error.code != "prohibited_advisory_content":
            raise
        _validate_override(db, user, override_reason=validator_override_reason)
        record_audit(
            db,
            action="advisory.validator_overridden",
            actor=user,
            entity_type="advisory",
            reason=validator_override_reason,
            detail={"violations": find_violations(f"{title}\n{body_md}")},
        )

    advisory = Advisory(
        crop_code=crop_code,
        target_code=target_code,
        geo_scope=scope,
        language=language,
        title=title.strip()[:300],
        status="draft",
        is_demo=False,
    )
    db.add(advisory)
    db.flush()

    version = AdvisoryVersion(
        advisory_id=advisory.id,
        version=1,
        body_md=body_md,
        action_types=action_types,
        author_id=user.id,
        source=source[:400],
        season=season,
        status="draft",
        valid_from=valid_from,
        valid_to=valid_to,
        content_hash=_content_hash(
            crop_code=crop_code,
            target_code=target_code,
            language=language,
            body=body_md,
        ),
    )
    db.add(version)
    db.flush()
    record_audit(
        db,
        action="advisory.created",
        actor=user,
        entity_type="advisory",
        entity_id=advisory.id,
        detail={"version": 1, "language": language},
    )
    return advisory


def add_version(
    db: Session,
    *,
    user: User,
    advisory_id: str,
    title: str | None,
    body_md: str,
    action_types: list[str],
    source: str,
    season: str | None,
    valid_from: datetime,
    valid_to: datetime,
    validator_override_reason: str | None,
) -> AdvisoryVersion:
    advisory = db.get(Advisory, advisory_id)
    if advisory is None:
        raise ApiError(404, "not_found", "Advisory not found")
    if advisory.status == "withdrawn":
        raise ApiError(409, "advisory_withdrawn", "A withdrawn advisory cannot be edited")
    _validate_target(db, advisory.crop_code, advisory.target_code)
    try:
        _validate_common(
            language=advisory.language,
            action_types=action_types,
            valid_from=valid_from,
            valid_to=valid_to,
            title=title or advisory.title,
            body=body_md,
        )
    except ApiError as error:
        if error.code != "prohibited_advisory_content":
            raise
        _validate_override(db, user, override_reason=validator_override_reason)
        record_audit(
            db,
            action="advisory.validator_overridden",
            actor=user,
            entity_type="advisory",
            entity_id=advisory.id,
            reason=validator_override_reason,
            detail={"violations": find_violations(f"{title or advisory.title}\n{body_md}")},
        )

    latest = db.scalar(
        select(AdvisoryVersion)
        .where(AdvisoryVersion.advisory_id == advisory.id)
        .order_by(AdvisoryVersion.version.desc())
    )
    next_number = (latest.version + 1) if latest else 1
    if title:
        advisory.title = title.strip()[:300]
    version = AdvisoryVersion(
        advisory_id=advisory.id,
        version=next_number,
        body_md=body_md,
        action_types=action_types,
        author_id=user.id,
        source=source[:400],
        season=season,
        status="draft",
        valid_from=valid_from,
        valid_to=valid_to,
        content_hash=_content_hash(
            crop_code=advisory.crop_code,
            target_code=advisory.target_code,
            language=advisory.language,
            body=body_md,
        ),
    )
    db.add(version)
    db.flush()
    record_audit(
        db,
        action="advisory.version_created",
        actor=user,
        entity_type="advisory",
        entity_id=advisory.id,
        detail={"version": next_number},
    )
    return version


def approve_version(
    db: Session,
    *,
    user: User,
    advisory_id: str,
    version_id: str,
    notes: str | None,
) -> AdvisoryVersion:
    if "can_approve_advisory" not in identity_service.active_permissions(db, user.id):
        raise ApiError(
            403,
            "forbidden",
            "The can_approve_advisory permission is required",
        )
    advisory = db.get(Advisory, advisory_id)
    if advisory is None:
        raise ApiError(404, "not_found", "Advisory not found")
    version = db.get(AdvisoryVersion, version_id)
    if version is None or version.advisory_id != advisory.id:
        raise ApiError(404, "not_found", "Advisory version not found")
    if version.status in {"published", "superseded"}:
        raise ApiError(409, "already_approved", "This version is already approved")
    if version.author_id == user.id:
        raise ApiError(
            403,
            "second_approver_required",
            "The author cannot be the sole approver",
        )
    if version.content_hash != _content_hash(
        crop_code=advisory.crop_code,
        target_code=advisory.target_code,
        language=advisory.language,
        body=version.body_md,
    ):
        raise ApiError(
            409,
            "content_hash_mismatch",
            "Advisory content changed after it was drafted; create a new version",
        )
    now = _now()
    if version.valid_to <= now:
        raise ApiError(422, "advisory_expired", "An expired version cannot be approved")
    if version.valid_from > version.valid_to:
        raise ApiError(422, "invalid_validity", "Advisory validity window is invalid")

    previous = (
        db.get(AdvisoryVersion, advisory.current_version_id)
        if advisory.current_version_id
        else None
    )
    if previous is not None and previous.id != version.id:
        previous.status = "superseded"

    version.status = "published"
    advisory.current_version_id = version.id
    advisory.status = "published"
    db.add(
        AdvisoryApproval(
            version_id=version.id,
            approver_id=user.id,
            role=user.active_role,
            notes=notes,
        )
    )
    record_audit(
        db,
        action="advisory.published",
        actor=user,
        entity_type="advisory",
        entity_id=advisory.id,
        detail={
            "version": version.version,
            "content_hash": version.content_hash,
            "valid_to": version.valid_to.isoformat(),
        },
    )
    return version


def withdraw(db: Session, *, user: User, advisory_id: str, reason: str) -> Advisory:
    if "can_approve_advisory" not in identity_service.active_permissions(db, user.id):
        raise ApiError(
            403,
            "forbidden",
            "The can_approve_advisory permission is required",
        )
    advisory = db.get(Advisory, advisory_id)
    if advisory is None:
        raise ApiError(404, "not_found", "Advisory not found")
    if not reason or len(reason.strip()) < 10:
        raise ApiError(422, "reason_required", "A withdrawal reason is required")
    advisory.status = "withdrawn"
    advisory.withdrawal_reason = reason
    for version in db.scalars(
        select(AdvisoryVersion).where(AdvisoryVersion.advisory_id == advisory.id)
    ).all():
        if version.status == "published":
            version.status = "withdrawn"
    record_audit(
        db,
        action="advisory.withdrawn",
        actor=user,
        entity_type="advisory",
        entity_id=advisory.id,
        reason=reason,
    )
    return advisory


def _serialize(advisory: Advisory, version: AdvisoryVersion, approval: AdvisoryApproval) -> dict:
    return {
        "advisory_id": advisory.id,
        "version_id": version.id,
        "version": version.version,
        "crop_code": advisory.crop_code,
        "target_code": advisory.target_code,
        "geo_scope": list(advisory.geo_scope),
        "language": advisory.language,
        "title": advisory.title,
        "body_md": version.body_md,
        "action_types": list(version.action_types),
        "source": version.source,
        "season": version.season,
        "valid_from": version.valid_from.isoformat(),
        "valid_to": version.valid_to.isoformat(),
        "content_hash": version.content_hash,
        "approved_by": approval.approver_id,
        "approved_at": approval.approved_at.isoformat(),
        "approval_notes": approval.notes,
        "is_demo": advisory.is_demo,
        "notice": "Approved non-chemical guidance. Not a diagnosis of your field.",
    }


def _serving_rows(
    db: Session,
    *,
    crop: str | None,
    target: str | None,
    geo: str | None,
    language: str,
) -> list[tuple[Advisory, AdvisoryVersion, AdvisoryApproval]]:
    now = _now()
    query = select(Advisory).where(Advisory.status == "published")
    if crop:
        query = query.where(Advisory.crop_code == crop)
    if target:
        query = query.where(Advisory.target_code == target)
    if language:
        query = query.where(Advisory.language == language)
    advisories = db.scalars(query).all()
    rows: list[tuple[Advisory, AdvisoryVersion, AdvisoryApproval]] = []
    for advisory in advisories:
        if advisory.current_version_id is None:
            continue
        version = db.get(AdvisoryVersion, advisory.current_version_id)
        if version is None or version.status != "published":
            continue
        approval = db.scalar(
            select(AdvisoryApproval).where(AdvisoryApproval.version_id == version.id)
        )
        if approval is None:
            continue
        if not (version.valid_from <= now <= version.valid_to):
            continue
        if geo and advisory.geo_scope and ALL_SUPPORTED_AREAS not in advisory.geo_scope:
            if geo not in advisory.geo_scope:
                continue
        rows.append((advisory, version, approval))
    return rows


def list_serving(
    db: Session,
    *,
    crop: str | None = None,
    target: str | None = None,
    geo: str | None = None,
    language: str = "en",
) -> dict:
    if language not in ALLOWED_LANGUAGES:
        raise ApiError(422, "unsupported_language", "Supported languages are en and kn")
    rows = _serving_rows(db, crop=crop, target=target, geo=geo, language=language)
    language_fallback = False
    if not rows and language != "en":
        rows = _serving_rows(db, crop=crop, target=target, geo=geo, language="en")
        language_fallback = bool(rows)
    items = [_serialize(*row) for row in rows]
    payload: dict = {
        "items": items,
        "requested_language": language,
        "language_fallback": language_fallback,
    }
    if not items:
        payload["fallback"] = {
            "message": "No approved advisory is available for this crop and area yet.",
            "next_step": "request_expert_review",
        }
    return payload


def list_drafts(db: Session, *, crop: str | None = None, target: str | None = None) -> dict:
    query = select(Advisory).where(Advisory.status != "withdrawn")
    if crop:
        query = query.where(Advisory.crop_code == crop)
    if target:
        query = query.where(Advisory.target_code == target)
    advisories = db.scalars(query.order_by(Advisory.updated_at.desc())).all()
    items = []
    for advisory in advisories:
        version = db.scalar(
            select(AdvisoryVersion)
            .where(AdvisoryVersion.advisory_id == advisory.id)
            .order_by(AdvisoryVersion.version.desc())
        )
        if version is None:
            continue
        approval = db.scalar(
            select(AdvisoryApproval).where(AdvisoryApproval.version_id == version.id)
        )
        items.append(
            {
                "advisory_id": advisory.id,
                "title": advisory.title,
                "crop_code": advisory.crop_code,
                "target_code": advisory.target_code,
                "language": advisory.language,
                "status": advisory.status,
                "latest_version": version.version,
                "latest_version_status": version.status,
                "approved": approval is not None,
                "valid_from": version.valid_from.isoformat(),
                "valid_to": version.valid_to.isoformat(),
                "updated_at": advisory.updated_at.isoformat(),
            }
        )
    return {"items": items}


def get_detail(db: Session, advisory_id: str) -> dict:
    advisory = db.get(Advisory, advisory_id)
    if advisory is None:
        raise ApiError(404, "not_found", "Advisory not found")
    versions = db.scalars(
        select(AdvisoryVersion)
        .where(AdvisoryVersion.advisory_id == advisory.id)
        .order_by(AdvisoryVersion.version.desc())
    ).all()
    return {
        "advisory_id": advisory.id,
        "title": advisory.title,
        "crop_code": advisory.crop_code,
        "target_code": advisory.target_code,
        "geo_scope": list(advisory.geo_scope),
        "language": advisory.language,
        "status": advisory.status,
        "withdrawal_reason": advisory.withdrawal_reason,
        "current_version_id": advisory.current_version_id,
        "versions": [
            {
                "version_id": row.id,
                "version": row.version,
                "status": row.status,
                "body_md": row.body_md,
                "action_types": list(row.action_types),
                "source": row.source,
                "season": row.season,
                "author_id": row.author_id,
                "content_hash": row.content_hash,
                "valid_from": row.valid_from.isoformat(),
                "valid_to": row.valid_to.isoformat(),
                "approved": db.scalar(
                    select(AdvisoryApproval).where(AdvisoryApproval.version_id == row.id)
                )
                is not None,
                "created_at": row.created_at.isoformat(),
            }
            for row in versions
        ],
    }


def valid_advisory_for_alert(
    db: Session, *, crop_code: str, target_code: str, geo_code: str
) -> tuple[Advisory, AdvisoryVersion] | None:
    rows = _serving_rows(
        db,
        crop=crop_code,
        target=target_code,
        geo=geo_code,
        language="en",
    )
    if not rows:
        return None
    advisory, version, _approval = rows[0]
    return advisory, version

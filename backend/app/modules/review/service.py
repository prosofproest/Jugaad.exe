"""Expert review queue, verification state machine and evidence rules."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.dependencies import assigned_area_codes
from app.core.errors import ApiError
from app.db.models import (
    Observation,
    ObservationVerification,
    Review,
    ReviewAssignment,
    ReviewEvent,
    ReviewEvidence,
    ReviewRequest,
    Target,
    User,
)
from app.modules import audit
from app.modules.assessment import service as assessment_service
from app.modules.identity import service as identity_service
from app.modules.media import storage
from app.modules.observations import service as observation_service
from sqlalchemy import select
from sqlalchemy.orm import Session

DECISIONS = ("confirmed", "probable", "rejected", "duplicate", "needs_visit", "unresolved")
QUEUE_STATUSES = ("uploaded", "assessed", "abstained", "pending_review")
LOCK_MINUTES = 15
SLA_HOURS = 48

REJECT_REASONS = {
    "not_a_plant",
    "healthy",
    "abiotic",
    "different_pest",
    "poor_image",
    "other",
}
UNRESOLVED_REASONS = {"poor_image", "conflicting_signs", "no_field_access", "other"}


def _now() -> datetime:
    return datetime.now(UTC)


def _require_reviewer(db: Session, user: User) -> list[str]:
    roles = identity_service.active_roles(db, user.id)
    if "extension_worker" not in roles and "admin" not in roles:
        raise ApiError(403, "forbidden", "Review requires a reviewer role")
    return roles


def _scope_observation(db: Session, user: User, observation_id: str) -> Observation:
    observation = observation_service.get_observation(db, observation_id)
    roles = identity_service.active_roles(db, user.id)
    if "admin" in roles:
        return observation
    if "extension_worker" not in roles:
        raise ApiError(403, "forbidden", "Review requires a reviewer role")
    if observation.area_code not in assigned_area_codes(db, user.id):
        raise ApiError(404, "not_found", "Observation not found")
    return observation


def _latest_prediction(db: Session, observation_id: str):
    return assessment_service.latest_prediction(db, observation_id)


def _urgency(db: Session, observation: Observation) -> float:
    prediction = _latest_prediction(db, observation.id)
    score = 0.45
    if prediction is not None and prediction.abstained:
        score += 0.25
    elif prediction is not None and prediction.confidence_band in {"low", "not_calibrated"}:
        score += 0.1
    age_hours = max(0.0, (_now() - observation.created_at).total_seconds() / 3600)
    score += min(age_hours / 240.0, 0.2)
    if age_hours > SLA_HOURS:
        score += 0.1
    return round(min(score, 1.0), 3)


def queue(
    db: Session,
    *,
    user: User,
    area_code: str | None,
    crop_code: str | None,
    status_filter: str | None,
    assigned_to_me: bool,
    overdue_only: bool,
    limit: int,
) -> dict:
    roles = _require_reviewer(db, user)
    query = select(Observation).where(
        Observation.deleted_at.is_(None),
        Observation.status.in_(QUEUE_STATUSES),
    )
    if "admin" not in roles:
        areas = assigned_area_codes(db, user.id)
        query = query.where(Observation.area_code.in_(areas or {""}))
    if area_code:
        query = query.where(Observation.area_code == area_code)
    if crop_code:
        query = query.where(Observation.crop_code == crop_code)
    if status_filter:
        query = query.where(Observation.status == status_filter)
    rows = db.scalars(query).all()

    if assigned_to_me:
        ids = {
            row.observation_id
            for row in db.scalars(
                select(ReviewAssignment).where(
                    ReviewAssignment.user_id == user.id,
                    ReviewAssignment.expires_at > _now(),
                )
            ).all()
        }
        rows = [row for row in rows if row.id in ids]
    if overdue_only:
        cutoff = _now() - timedelta(hours=SLA_HOURS)
        rows = [row for row in rows if row.created_at < cutoff]

    items = []
    for row in rows:
        prediction = _latest_prediction(db, row.id)
        items.append(
            {
                "observation_id": row.id,
                "crop_code": row.crop_code,
                "area_code": row.area_code,
                "status": row.status,
                "created_at": row.created_at.isoformat(),
                "age_hours": round((_now() - row.created_at).total_seconds() / 3600, 1),
                "overdue": row.created_at < _now() - timedelta(hours=SLA_HOURS),
                "urgency": _urgency(db, row),
                "model_abstained": bool(prediction and prediction.abstained),
                "abstain_reason": prediction.abstain_reason if prediction else None,
                "quality_flags": list(prediction.quality_flags) if prediction else [],
            }
        )
    items.sort(key=lambda item: (-item["urgency"], item["created_at"]))
    return {"items": items[:limit], "next_cursor": None}


def queue_summary(db: Session, *, user: User) -> dict:
    roles = _require_reviewer(db, user)
    query = select(Observation).where(
        Observation.deleted_at.is_(None), Observation.status.in_(QUEUE_STATUSES)
    )
    if "admin" not in roles:
        areas = assigned_area_codes(db, user.id)
        query = query.where(Observation.area_code.in_(areas or {""}))
    rows = db.scalars(query).all()
    now = _now()
    ages = sorted((now - row.created_at).total_seconds() / 3600 for row in rows)
    median = ages[len(ages) // 2] if ages else 0.0
    by_area: dict[str, int] = {}
    for row in rows:
        by_area[row.area_code] = by_area.get(row.area_code, 0) + 1
    return {
        "backlog": len(rows),
        "median_age_hours": round(median, 1),
        "overdue": sum(1 for row in rows if row.created_at < now - timedelta(hours=SLA_HOURS)),
        "by_area": by_area,
        "sla_hours": SLA_HOURS,
    }


def claim(db: Session, *, user: User, observation_id: str) -> dict:
    _require_reviewer(db, user)
    observation = _scope_observation(db, user, observation_id)
    existing = db.scalar(
        select(ReviewAssignment)
        .where(ReviewAssignment.observation_id == observation.id)
        .order_by(ReviewAssignment.assigned_at.desc())
    )
    now = _now()
    if existing is not None and existing.expires_at > now:
        if existing.user_id != user.id:
            raise ApiError(409, "case_locked", "Another reviewer has this case")
        existing.expires_at = now + timedelta(minutes=LOCK_MINUTES)
        return {
            "observation_id": observation.id,
            "claimed_by": user.id,
            "expires_at": existing.expires_at.isoformat(),
        }
    assignment = ReviewAssignment(
        observation_id=observation.id,
        user_id=user.id,
        area_code=observation.area_code,
        expires_at=now + timedelta(minutes=LOCK_MINUTES),
    )
    db.add(assignment)
    audit.record_audit(
        db,
        action="review.claimed",
        actor=user,
        entity_type="observation",
        entity_id=observation.id,
    )
    return {
        "observation_id": observation.id,
        "claimed_by": user.id,
        "expires_at": assignment.expires_at.isoformat(),
    }


def _allowed_decisions(db: Session, user: User) -> list[str]:
    roles = identity_service.active_roles(db, user.id)
    if "admin" in roles:
        return []
    decisions = ["probable", "rejected", "duplicate", "needs_visit", "unresolved"]
    if identity_service.active_permissions(db, user.id) & {"can_confirm"}:
        decisions.insert(0, "confirmed")
    return decisions


def case_detail(db: Session, *, user: User, observation_id: str) -> dict:
    _require_reviewer(db, user)
    observation = _scope_observation(db, user, observation_id)
    image = assessment_service.latest_image(db, observation.id)
    download = None
    if image is not None:
        download = storage.download_descriptor(
            observation_id=observation.id, image_id=image.id, key=image.storage_key
        )
    events = db.scalars(
        select(ReviewEvent)
        .where(ReviewEvent.observation_id == observation.id)
        .order_by(ReviewEvent.created_at)
    ).all()
    requests = db.scalars(
        select(ReviewRequest)
        .where(ReviewRequest.observation_id == observation.id)
        .order_by(ReviewRequest.created_at)
    ).all()
    assignment = db.scalar(
        select(ReviewAssignment)
        .where(ReviewAssignment.observation_id == observation.id)
        .order_by(ReviewAssignment.assigned_at.desc())
    )
    return {
        "observation": observation_service.serialize_observation(db, observation),
        "image": download,
        "assessment": assessment_service.assessment_payload(db, observation),
        "context": {
            "crop_code": observation.crop_code,
            "area_code": observation.area_code,
            "growth_stage": observation.growth_stage,
            "variety": observation.variety,
            "notes": observation.notes,
            "captured_at": observation.captured_at.isoformat() if observation.captured_at else None,
            "area_level_only": True,
        },
        "history": [
            {
                "event_id": event.id,
                "from_status": event.from_status,
                "to_status": event.to_status,
                "actor_id": event.actor_id,
                "reason": event.reason,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ],
        "review_requests": [
            {
                "id": request.id,
                "requested_by": request.requested_by,
                "reason": request.reason,
                "status": request.status,
                "created_at": request.created_at.isoformat(),
            }
            for request in requests
        ],
        "allowed_decisions": _allowed_decisions(db, user),
        "lock": (
            {
                "user_id": assignment.user_id,
                "expires_at": assignment.expires_at.isoformat(),
                "held_by_me": assignment.user_id == user.id,
            }
            if assignment is not None and assignment.expires_at > _now()
            else None
        ),
        "not_a_diagnosis": True,
    }


def _check_lock(db: Session, user: User, observation_id: str) -> None:
    assignment = db.scalar(
        select(ReviewAssignment)
        .where(ReviewAssignment.observation_id == observation_id)
        .order_by(ReviewAssignment.assigned_at.desc())
    )
    if assignment is not None and assignment.expires_at > _now() and assignment.user_id != user.id:
        raise ApiError(409, "case_locked", "Another reviewer has this case")


def _validate_evidence(
    *, decision: str, evidence: dict, reason_code: str | None, note: str | None
) -> list[ReviewEvidence]:
    image_note = (evidence.get("image_note") or "").strip()
    field_observation = (evidence.get("field_observation") or "").strip()
    lab_confirmation = (evidence.get("lab_confirmation") or "").strip()
    rows: list[ReviewEvidence] = []

    if decision == "confirmed":
        if not image_note or not (field_observation or lab_confirmation):
            raise ApiError(
                422,
                "evidence_required",
                "Confirmed requires an image note and field or lab evidence",
            )
    elif decision == "probable":
        if not image_note or not field_observation:
            raise ApiError(
                422,
                "evidence_required",
                "Probable requires an image note and a supporting field observation",
            )
    elif decision == "rejected":
        if reason_code not in REJECT_REASONS or not note:
            raise ApiError(
                422,
                "reason_required",
                "Rejected requires a valid reason code and a note",
            )
    elif decision == "unresolved":
        if reason_code not in UNRESOLVED_REASONS or not note:
            raise ApiError(
                422,
                "reason_required",
                "Unresolved requires a valid reason code and a note",
            )
    elif decision == "needs_visit":
        if not note:
            raise ApiError(422, "reason_required", "Needs visit requires a reason")

    if image_note:
        rows.append(ReviewEvidence(type="image_note", value=image_note, source="reviewer"))
    if field_observation:
        rows.append(
            ReviewEvidence(type="field_observation", value=field_observation, source="reviewer")
        )
    if lab_confirmation:
        rows.append(ReviewEvidence(type="lab_result", value=lab_confirmation, source="reviewer"))
    return rows


def decide(
    db: Session,
    *,
    user: User,
    observation_id: str,
    decision: str,
    corrected_label: str | None,
    severity: str | None,
    evidence: dict,
    reason_code: str | None,
    note: str | None,
    duplicate_of: str | None,
    client_request_id: str | None,
) -> dict:
    roles = _require_reviewer(db, user)
    if "admin" in roles:
        # Separation of duties: admin cannot set verification status.
        raise ApiError(403, "forbidden", "Admins cannot set verification status")
    observation = _scope_observation(db, user, observation_id)

    if client_request_id:
        existing = db.scalar(
            select(Review).where(
                Review.observation_id == observation.id,
                Review.client_request_id == client_request_id,
            )
        )
        if existing is not None:
            verification = db.get(ObservationVerification, observation.id)
            return {
                "review_id": existing.id,
                "decision": existing.decision,
                "observation_id": observation.id,
                "verification_status": verification.status if verification else existing.decision,
                "event_id": None,
                "idempotent_replay": True,
            }

    if decision not in DECISIONS:
        raise ApiError(422, "invalid_decision", "Unknown verification decision")
    if decision == "confirmed" and "can_confirm" not in identity_service.active_permissions(
        db, user.id
    ):
        raise ApiError(
            403,
            "forbidden",
            "The can_confirm permission is required for confirmed",
        )
    if decision == "duplicate":
        if not duplicate_of:
            raise ApiError(422, "duplicate_target_required", "A canonical case is required")
        canonical = db.get(Observation, duplicate_of)
        if canonical is None or canonical.id == observation.id:
            raise ApiError(422, "invalid_duplicate", "Canonical observation is not valid")
    _check_lock(db, user, observation.id)

    if corrected_label:
        target = db.scalar(
            select(Target).where(
                Target.crop_code == observation.crop_code,
                Target.code == corrected_label,
                Target.supported.is_(True),
            )
        )
        if target is None:
            raise ApiError(422, "invalid_label", "Corrected label is not in the allowlist")

    evidence_rows = _validate_evidence(
        decision=decision, evidence=evidence or {}, reason_code=reason_code, note=note
    )

    previous_status = observation.status
    review = Review(
        observation_id=observation.id,
        reviewer_id=user.id,
        decision=decision,
        reason_code=reason_code,
        corrected_label=corrected_label,
        severity=severity,
        note=note,
        duplicate_of=duplicate_of,
        client_request_id=client_request_id,
    )
    db.add(review)
    db.flush()
    for row in evidence_rows:
        row.review_id = review.id
        db.add(row)

    event = ReviewEvent(
        observation_id=observation.id,
        from_status=previous_status,
        to_status=decision,
        actor_id=user.id,
        reason=note or reason_code,
    )
    db.add(event)
    observation.status = "reviewed"

    verification = db.get(ObservationVerification, observation.id)
    if verification is None:
        verification = ObservationVerification(observation_id=observation.id)
        db.add(verification)
    verification.status = decision
    verification.evidence_tier = decision
    verification.verified_at = _now()
    verification.verified_by = user.id
    verification.review_id = review.id
    verification.updated_at = _now()

    assignment = db.scalar(
        select(ReviewAssignment)
        .where(ReviewAssignment.observation_id == observation.id)
        .order_by(ReviewAssignment.assigned_at.desc())
    )
    if assignment is not None:
        assignment.expires_at = _now()

    open_request = db.scalar(
        select(ReviewRequest).where(
            ReviewRequest.observation_id == observation.id,
            ReviewRequest.status == "open",
        )
    )
    if open_request is not None:
        open_request.status = "decided"

    audit.record_audit(
        db,
        action="review.decision_recorded",
        actor=user,
        entity_type="observation",
        entity_id=observation.id,
        reason=note,
        detail={
            "decision": decision,
            "review_id": review.id,
            "evidence_types": [row.type for row in evidence_rows],
            "model_output_copied": False,
        },
    )
    db.flush()
    return {
        "review_id": review.id,
        "decision": decision,
        "observation_id": observation.id,
        "verification_status": decision,
        "event_id": event.id,
        "idempotent_replay": False,
    }


def escalate(db: Session, *, user: User, observation_id: str, note: str) -> dict:
    observation = _scope_observation(db, user, observation_id)
    event = ReviewEvent(
        observation_id=observation.id,
        from_status=observation.status,
        to_status="pending_review",
        actor_id=user.id,
        reason=f"escalated: {note}",
    )
    db.add(event)
    observation.status = "pending_review"
    audit.record_audit(
        db,
        action="review.escalated",
        actor=user,
        entity_type="observation",
        entity_id=observation.id,
        reason=note,
    )
    return {"observation_id": observation.id, "event_id": event.id, "status": observation.status}


def request_info(db: Session, *, user: User, observation_id: str, message: str) -> dict:
    observation = _scope_observation(db, user, observation_id)
    event = ReviewEvent(
        observation_id=observation.id,
        from_status=observation.status,
        to_status=observation.status,
        actor_id=user.id,
        reason=f"info_requested: {message}",
    )
    db.add(event)
    audit.record_audit(
        db,
        action="review.info_requested",
        actor=user,
        entity_type="observation",
        entity_id=observation.id,
        reason=message,
    )
    return {"observation_id": observation.id, "event_id": event.id}


def events(db: Session, *, user: User, observation_id: str) -> dict:
    observation = _scope_observation(db, user, observation_id)
    rows = db.scalars(
        select(ReviewEvent)
        .where(ReviewEvent.observation_id == observation.id)
        .order_by(ReviewEvent.created_at)
    ).all()
    return {
        "items": [
            {
                "id": row.id,
                "from_status": row.from_status,
                "to_status": row.to_status,
                "actor_id": row.actor_id,
                "reason": row.reason,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }

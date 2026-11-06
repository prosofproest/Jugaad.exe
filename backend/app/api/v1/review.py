"""Expert review routes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.models import ReviewAssignment, User
from app.db.session import get_db
from app.modules.review import service

router = APIRouter(prefix="/reviews", tags=["reviews"])


class ClaimRequest(BaseModel):
    action: Literal["claim", "unclaim"] = "claim"


class Evidence(BaseModel):
    image_note: str | None = None
    field_observation: str | None = None
    lab_confirmation: str | None = None


class DecisionRequest(BaseModel):
    decision: str
    corrected_label: str | None = None
    severity: str | None = None
    evidence: Evidence = Field(default_factory=Evidence)
    reason_code: str | None = None
    note: str | None = None
    duplicate_of: str | None = None
    client_request_id: str | None = None


class NoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=2000)


@router.get("/queue")
def get_queue(
    area_code: str | None = None,
    crop_code: str | None = None,
    status: str | None = None,
    assigned_to_me: bool = False,
    overdue_only: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_roles("extension_worker", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    return service.queue(
        db,
        user=user,
        area_code=area_code,
        crop_code=crop_code,
        status_filter=status,
        assigned_to_me=assigned_to_me,
        overdue_only=overdue_only,
        limit=limit,
    )


@router.get("/queue/summary")
def get_queue_summary(
    user: User = Depends(require_roles("extension_worker", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    return service.queue_summary(db, user=user)


@router.post("/{observation_id}/claim")
def claim_case(
    observation_id: str,
    payload: ClaimRequest,
    user: User = Depends(require_roles("extension_worker", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    if payload.action == "unclaim":
        # Admins may release a stale lock; reviewers may release their own.
        observation = service._scope_observation(db, user, observation_id)  # noqa: SLF001
        assignment = db.scalar(
            select(ReviewAssignment)
            .where(ReviewAssignment.observation_id == observation.id)
            .order_by(ReviewAssignment.assigned_at.desc())
        )
        if assignment is not None:
            assignment.expires_at = datetime.now(UTC)
        db.commit()
        return {"observation_id": observation.id, "claimed_by": None}
    result = service.claim(db, user=user, observation_id=observation_id)
    db.commit()
    return result


@router.get("/{observation_id}")
def get_case(
    observation_id: str,
    user: User = Depends(require_roles("extension_worker", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    return service.case_detail(db, user=user, observation_id=observation_id)


@router.post("/{observation_id}/decisions")
def record_decision(
    observation_id: str,
    payload: DecisionRequest,
    user: User = Depends(require_roles("extension_worker", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    result = service.decide(
        db,
        user=user,
        observation_id=observation_id,
        decision=payload.decision,
        corrected_label=payload.corrected_label,
        severity=payload.severity,
        evidence=payload.evidence.model_dump(),
        reason_code=payload.reason_code,
        note=payload.note,
        duplicate_of=payload.duplicate_of,
        client_request_id=payload.client_request_id,
    )
    db.commit()
    return result


@router.post("/{observation_id}/escalate")
def escalate(
    observation_id: str,
    payload: NoteRequest,
    user: User = Depends(require_roles("extension_worker", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    result = service.escalate(db, user=user, observation_id=observation_id, note=payload.note)
    db.commit()
    return result


@router.post("/{observation_id}/request-info")
def request_info(
    observation_id: str,
    payload: NoteRequest,
    user: User = Depends(require_roles("extension_worker", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    result = service.request_info(
        db, user=user, observation_id=observation_id, message=payload.note
    )
    db.commit()
    return result


@router.get("/{observation_id}/events")
def get_events(
    observation_id: str,
    user: User = Depends(require_roles("extension_worker", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    return service.events(db, user=user, observation_id=observation_id)

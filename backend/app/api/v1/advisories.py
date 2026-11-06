"""Approved advisory retrieval and the authoring/approval workflow."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    require_any_role_or_permission,
    require_roles,
)
from app.db.models import User
from app.db.session import get_db
from app.modules.advisories import service

router = APIRouter(prefix="/advisories", tags=["advisories"])
admin_router = APIRouter(prefix="/admin/advisories", tags=["admin"])


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class AdvisoryCreate(BaseModel):
    crop_code: str
    target_code: str
    geo_scope: list[str] = Field(default_factory=list)
    language: str = "en"
    title: str = Field(min_length=3, max_length=300)
    body_md: str = Field(min_length=10, max_length=20000)
    action_types: list[str]
    source: str = Field(min_length=3, max_length=400)
    season: str | None = Field(default=None, max_length=40)
    valid_from: datetime
    valid_to: datetime
    validator_override_reason: str | None = None


class AdvisoryVersionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    body_md: str = Field(min_length=10, max_length=20000)
    action_types: list[str]
    source: str = Field(min_length=3, max_length=400)
    season: str | None = Field(default=None, max_length=40)
    valid_from: datetime
    valid_to: datetime
    validator_override_reason: str | None = None


class ApprovalRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)


class WithdrawalRequest(BaseModel):
    reason: str = Field(min_length=10, max_length=2000)


@router.get("")
def list_advisories(
    crop: str | None = None,
    target: str | None = None,
    geo: str | None = None,
    language: str = Query(default="en", max_length=2),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return service.list_serving(
        db, crop=crop, target=target, geo=geo, language=language
    )


@admin_router.get("")
def list_drafts(
    crop: str | None = None,
    target: str | None = None,
    user: User = Depends(require_roles("extension_worker", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    return service.list_drafts(db, crop=crop, target=target)


@router.get("/{advisory_id}")
def get_advisory(
    advisory_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return service.get_detail(db, advisory_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_advisory(
    payload: AdvisoryCreate,
    user: User = Depends(require_roles("extension_worker", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    advisory = service.create_advisory(
        db,
        user=user,
        crop_code=payload.crop_code,
        target_code=payload.target_code,
        geo_scope=payload.geo_scope,
        language=payload.language,
        title=payload.title,
        body_md=payload.body_md,
        action_types=payload.action_types,
        source=payload.source,
        season=payload.season,
        valid_from=_aware(payload.valid_from),
        valid_to=_aware(payload.valid_to),
        validator_override_reason=payload.validator_override_reason,
    )
    db.commit()
    return service.get_detail(db, advisory.id)


@router.post("/{advisory_id}/versions", status_code=status.HTTP_201_CREATED)
def create_version(
    advisory_id: str,
    payload: AdvisoryVersionCreate,
    user: User = Depends(require_roles("extension_worker", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    version = service.add_version(
        db,
        user=user,
        advisory_id=advisory_id,
        title=payload.title,
        body_md=payload.body_md,
        action_types=payload.action_types,
        source=payload.source,
        season=payload.season,
        valid_from=_aware(payload.valid_from),
        valid_to=_aware(payload.valid_to),
        validator_override_reason=payload.validator_override_reason,
    )
    db.commit()
    return {
        "advisory_id": advisory_id,
        "version_id": version.id,
        "version": version.version,
        "status": version.status,
    }


@router.post("/{advisory_id}/versions/{version_id}/approve")
def approve_version(
    advisory_id: str,
    version_id: str,
    payload: ApprovalRequest,
    user: User = Depends(require_any_role_or_permission([], "can_approve_advisory")),
    db: Session = Depends(get_db),
) -> dict:
    version = service.approve_version(
        db,
        user=user,
        advisory_id=advisory_id,
        version_id=version_id,
        notes=payload.notes,
    )
    db.commit()
    return {
        "advisory_id": advisory_id,
        "version_id": version.id,
        "version": version.version,
        "status": version.status,
        "valid_from": version.valid_from.isoformat(),
        "valid_to": version.valid_to.isoformat(),
    }


@router.post("/{advisory_id}/withdraw")
def withdraw_advisory(
    advisory_id: str,
    payload: WithdrawalRequest,
    user: User = Depends(require_any_role_or_permission([], "can_approve_advisory")),
    db: Session = Depends(get_db),
) -> dict:
    advisory = service.withdraw(
        db, user=user, advisory_id=advisory_id, reason=payload.reason
    )
    db.commit()
    return {
        "advisory_id": advisory.id,
        "status": advisory.status,
        "withdrawal_reason": advisory.withdrawal_reason,
    }

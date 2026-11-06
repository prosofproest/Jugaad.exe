"""Observation, catalogue, area and media routes."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import (
    get_current_user,
    require_idempotency_key,
    require_roles,
)
from app.core.errors import ApiError
from app.db.models import Crop, Geography, GrowingArea, ImageAsset, User, UserAreaAssignment
from app.db.session import get_db
from app.modules.assessment import service as assessment_service
from app.modules.audit.service import record_audit
from app.modules.identity import service as identity_service
from app.modules.media import storage
from app.modules.observations import service as observation_service

router = APIRouter(tags=["observations"])


class ObservationCreate(BaseModel):
    client_report_id: str = Field(min_length=8, max_length=128)
    crop_code: str
    area_code: str
    variety: str | None = None
    growth_stage: str | None = None
    notes: str | None = Field(default=None, max_length=2000)
    captured_at: datetime | None = None
    subject_user_id: str | None = None


class UploadUrlRequest(BaseModel):
    content_type: str
    size_bytes: int = Field(gt=0)
    content_hash: str | None = None
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    source: Literal["camera", "gallery"] = "camera"
    compression: dict | None = None


class ReviewRequestBody(BaseModel):
    reason: str | None = Field(default=None, max_length=300)


def _require_admin_reason(
    db: Session, user: User, observation, reason: str | None, request: Request
) -> None:
    roles = identity_service.active_roles(db, user.id)
    if "admin" not in roles:
        return
    if observation.user_id == user.id:
        return
    if not reason:
        raise ApiError(
            400,
            "reason_required",
            "Admin access to an individual record requires a reason",
        )
    record_audit(
        db,
        action="admin.record_viewed",
        actor=user,
        entity_type="observation",
        entity_id=observation.id,
        reason=reason,
        detail={"path": request.url.path},
    )


@router.get("/config/crops")
def list_crops(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    crops = db.scalars(select(Crop).order_by(Crop.code)).all()
    return {
        "items": [observation_service.catalogue_entry(db, crop) for crop in crops],
        "note": "Open crop catalogue. Only supported crop x target pairs are assessed.",
    }


@router.get("/areas")
def list_areas(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    geographies = db.scalars(select(Geography).order_by(Geography.code)).all()
    saved = db.scalars(select(GrowingArea).where(GrowingArea.owner_user_id == user.id)).all()
    assignment_rows = db.scalars(
        select(UserAreaAssignment).where(UserAreaAssignment.user_id == user.id)
    ).all()
    return {
        "geographies": [
            {
                "code": row.code,
                "level": row.level,
                "name": row.name,
                "parent_code": row.parent_code,
                "boundary_version": row.boundary_version,
            }
            for row in geographies
        ],
        "saved_areas": [
            {
                "id": row.id,
                "geo_code": row.geo_code,
                "precision": row.precision,
                "label": row.label,
            }
            for row in saved
        ],
        "assignment_scope": sorted({row.geo_code for row in assignment_rows}),
        "privacy": "Approximate block/mandal area only; no farm coordinates are returned.",
    }


@router.post("/observations", status_code=status.HTTP_201_CREATED)
def create_observation(
    payload: ObservationCreate,
    response: Response,
    idempotency_key: str = Depends(require_idempotency_key),
    user: User = Depends(require_roles("farmer", "extension_worker")),
    db: Session = Depends(get_db),
) -> dict:
    observation, created = observation_service.create_observation(
        db,
        user=user,
        client_report_id=payload.client_report_id,
        crop_code=payload.crop_code,
        area_code=payload.area_code,
        variety=payload.variety,
        growth_stage=payload.growth_stage,
        notes=payload.notes,
        captured_at=payload.captured_at,
        subject_user_id=payload.subject_user_id,
        idempotency_key=idempotency_key,
    )
    db.commit()
    if not created:
        response.status_code = status.HTTP_200_OK
    return observation_service.serialize_observation(db, observation)


@router.get("/observations")
def list_observations(
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return observation_service.list_observations(
        db, user=user, cursor=cursor, limit=limit, status_filter=status_filter
    )


@router.get("/observations/{observation_id}")
def get_observation(
    observation_id: str,
    request: Request,
    reason: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    observation = observation_service.readable_observation(db, user, observation_id)
    _require_admin_reason(db, user, observation, reason, request)
    db.commit()
    return observation_service.serialize_observation(db, observation)


@router.get("/observations/{observation_id}/assessment")
def get_assessment(
    observation_id: str,
    request: Request,
    reason: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    observation = observation_service.readable_observation(db, user, observation_id)
    _require_admin_reason(db, user, observation, reason, request)
    payload = assessment_service.assessment_payload(db, observation)
    db.commit()
    return payload


@router.post("/observations/{observation_id}/images/upload-url")
def create_upload_url(
    observation_id: str,
    payload: UploadUrlRequest,
    user: User = Depends(require_roles("farmer", "extension_worker")),
    db: Session = Depends(get_db),
) -> dict:
    observation = observation_service.writable_observation(db, user, observation_id)
    result = observation_service.create_upload_url(
        db,
        user=user,
        observation=observation,
        content_type=payload.content_type,
        size_bytes=payload.size_bytes,
        content_hash=payload.content_hash,
        width=payload.width,
        height=payload.height,
        source=payload.source,
        compression=payload.compression,
    )
    db.commit()
    return result


@router.put("/uploads/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def upload_bytes(token: str, request: Request, db: Session = Depends(get_db)) -> None:
    payload = storage.verify_upload_token(token)
    data = await request.body()
    if not data:
        raise ApiError(400, "empty_upload", "Upload body is empty")
    if len(data) > get_settings().max_upload_bytes:
        raise ApiError(413, "image_too_large", "Upload exceeds the configured size limit")
    storage.write_bytes(payload["key"], data)
    image = db.get(ImageAsset, payload.get("image_id"))
    if image is None or image.observation_id != payload.get("observation_id"):
        raise ApiError(404, "not_found", "Image not found")
    db.commit()


@router.post("/observations/{observation_id}/images/{image_id}/complete")
def complete_upload(
    observation_id: str,
    image_id: str,
    user: User = Depends(require_roles("farmer", "extension_worker")),
    db: Session = Depends(get_db),
) -> dict:
    observation = observation_service.writable_observation(db, user, observation_id)
    result = observation_service.complete_upload(
        db, user=user, observation=observation, image_id=image_id
    )
    db.commit()
    result["assessment"] = assessment_service.assessment_payload(db, observation)
    return result


@router.get("/observations/{observation_id}/images/{image_id}/download-url")
def download_url(
    observation_id: str,
    image_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    observation = observation_service.readable_observation(db, user, observation_id)
    image = db.get(ImageAsset, image_id)
    if image is None or image.observation_id != observation.id:
        raise ApiError(404, "not_found", "Image not found")
    return storage.download_descriptor(
        observation_id=observation.id, image_id=image.id, key=image.storage_key
    )


@router.get("/uploads/download/{token}")
def download_bytes(token: str, db: Session = Depends(get_db)) -> Response:
    payload = storage.verify_download_token(token)
    image = db.get(ImageAsset, payload.get("image_id"))
    if image is None or image.observation_id != payload.get("observation_id"):
        raise ApiError(404, "not_found", "Image not found")
    data = storage.read_bytes(payload["key"])
    return Response(content=data, media_type=image.mime)


@router.post("/observations/{observation_id}/review-request", status_code=status.HTTP_201_CREATED)
def create_review_request(
    observation_id: str,
    payload: ReviewRequestBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    observation = observation_service.readable_observation(db, user, observation_id)
    request = observation_service.request_review(
        db, user=user, observation=observation, reason=payload.reason
    )
    db.commit()
    return {
        "review_request_id": request.id,
        "observation_id": observation.id,
        "status": request.status,
        "submitted_at": request.created_at.isoformat(),
    }

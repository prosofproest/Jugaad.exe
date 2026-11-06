"""Observation creation, media intake and review requests."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.config import get_settings
from app.core.dependencies import assigned_area_codes, can_read_observation
from app.core.errors import ApiError
from app.core.idempotency import find_existing, remember
from app.db.models import (
    Crop,
    Geography,
    ImageAsset,
    Observation,
    ObservationVerification,
    ReviewEvent,
    ReviewRequest,
    Target,
    User,
)
from app.modules.assessment import service as assessment_service
from app.modules.audit.service import record_audit
from app.modules.identity import service as identity_service
from app.modules.media import storage
from sqlalchemy import or_, select
from sqlalchemy.orm import Session


def _now() -> datetime:
    return datetime.now(UTC)


def get_observation(db: Session, observation_id: str) -> Observation:
    observation = db.get(Observation, observation_id)
    if observation is None or observation.deleted_at is not None:
        raise ApiError(404, "not_found", "Observation not found")
    return observation


def readable_observation(db: Session, user: User, observation_id: str) -> Observation:
    observation = get_observation(db, observation_id)
    if not can_read_observation(db, user, observation):
        # Cross-user access is deliberately indistinguishable from absence.
        raise ApiError(404, "not_found", "Observation not found")
    return observation


def writable_observation(db: Session, user: User, observation_id: str) -> Observation:
    observation = get_observation(db, observation_id)
    roles = identity_service.active_roles(db, user.id)
    owns = observation.user_id == user.id or observation.subject_user_id == user.id
    if owns:
        return observation
    if "extension_worker" in roles and observation.area_code in assigned_area_codes(db, user.id):
        return observation
    raise ApiError(404, "not_found", "Observation not found")


def serialize_observation(db: Session, observation: Observation) -> dict:
    verification = db.get(ObservationVerification, observation.id)
    return {
        "id": observation.id,
        "client_report_id": observation.client_report_id,
        "status": observation.status,
        "crop_code": observation.crop_code,
        "area_code": observation.area_code,
        "variety": observation.variety,
        "growth_stage": observation.growth_stage,
        "notes": observation.notes,
        "captured_at": observation.captured_at.isoformat() if observation.captured_at else None,
        "submitted_at": observation.submitted_at.isoformat(),
        "is_demo": observation.is_demo,
        "verification": {
            "status": verification.status if verification else "unverified",
            "evidence_tier": verification.evidence_tier if verification else "unverified",
        },
        "created_at": observation.created_at.isoformat(),
    }


def create_observation(
    db: Session,
    *,
    user: User,
    client_report_id: str,
    crop_code: str,
    area_code: str,
    variety: str | None,
    growth_stage: str | None,
    notes: str | None,
    captured_at: datetime | None,
    subject_user_id: str | None,
    idempotency_key: str,
) -> tuple[Observation, bool]:
    missing = identity_service.missing_required_consents(db, user.id)
    if missing:
        raise ApiError(
            403,
            "consent_required",
            "Consent is required before the first report",
            detail=f"Missing consent(s): {', '.join(missing)}",
        )

    roles = identity_service.active_roles(db, user.id)
    if "farmer" not in roles and "extension_worker" not in roles:
        raise ApiError(403, "forbidden", "Your role cannot create observations")

    if db.get(Crop, crop_code) is None:
        raise ApiError(422, "unknown_crop", "Crop is not in the open catalogue")
    if db.scalar(select(Geography).where(Geography.code == area_code)) is None:
        raise ApiError(422, "unknown_area", "Area code is not recognised")

    if subject_user_id:
        if "extension_worker" not in roles:
            raise ApiError(403, "forbidden", "Only extension workers can capture on behalf")
        subject = db.get(User, subject_user_id)
        if subject is None:
            raise ApiError(422, "unknown_subject", "Farmer to capture for was not found")

    existing = db.scalar(
        select(Observation).where(
            Observation.user_id == user.id,
            Observation.client_report_id == client_report_id,
        )
    )
    if existing is not None:
        return existing, False

    record = find_existing(db, user_id=user.id, scope="observation.create", key=idempotency_key)
    if record is not None:
        if record.entity_id:
            existing = db.get(Observation, record.entity_id)
            if existing is not None:
                return existing, False

    observation = Observation(
        client_report_id=client_report_id,
        user_id=user.id,
        subject_user_id=subject_user_id,
        area_code=area_code,
        crop_code=crop_code,
        variety=variety,
        growth_stage=growth_stage,
        notes=None if notes is None else notes[:2000],
        captured_at=captured_at,
        status="pending_upload",
        is_demo=False,
    )
    db.add(observation)
    db.flush()
    db.add(
        ObservationVerification(
            observation_id=observation.id,
            status="unverified",
            evidence_tier="unverified",
        )
    )
    remember(
        db,
        user_id=user.id,
        scope="observation.create",
        key=idempotency_key,
        entity_id=observation.id,
    )
    record_audit(
        db,
        action="observation.created",
        actor=user,
        entity_type="observation",
        entity_id=observation.id,
        detail={"crop_code": crop_code, "area_code": area_code},
    )
    return observation, True


def list_observations(
    db: Session,
    *,
    user: User,
    cursor: str | None,
    limit: int = 50,
    status_filter: str | None = None,
) -> dict:
    roles = identity_service.active_roles(db, user.id)
    query = select(Observation).where(Observation.deleted_at.is_(None))
    if "admin" in roles:
        pass
    elif "extension_worker" in roles:
        areas = assigned_area_codes(db, user.id)
        query = query.where(
            or_(Observation.user_id == user.id, Observation.area_code.in_(areas or {""}))
        )
    else:
        query = query.where(Observation.user_id == user.id)
    if status_filter:
        query = query.where(Observation.status == status_filter)
    if cursor:
        query = query.where(Observation.created_at < _parse_cursor(cursor))
    rows = db.scalars(query.order_by(Observation.created_at.desc()).limit(limit + 1)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    return {
        "items": [serialize_observation(db, row) for row in rows],
        "next_cursor": rows[-1].created_at.isoformat() if has_more and rows else None,
    }


def _parse_cursor(cursor: str) -> datetime:
    try:
        value = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
    except ValueError as error:
        raise ApiError(422, "invalid_cursor", "Cursor is not a valid timestamp") from error
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def create_upload_url(
    db: Session,
    *,
    user: User,
    observation: Observation,
    content_type: str,
    size_bytes: int,
    content_hash: str | None,
    width: int | None,
    height: int | None,
    source: str,
    compression: dict | None,
) -> dict:
    settings = get_settings()
    if content_type not in settings.allowed_image_types:
        raise ApiError(422, "unsupported_image_type", "Image type is not accepted")
    if size_bytes <= 0 or size_bytes > settings.max_upload_bytes:
        raise ApiError(422, "image_too_large", "Image exceeds the configured size limit")

    image = ImageAsset(
        observation_id=observation.id,
        storage_key="pending",
        original_width=width,
        original_height=height,
        bytes=size_bytes,
        content_hash=content_hash,
        mime=content_type,
        source=source if source in {"camera", "gallery"} else "camera",
        compression=compression or {},
        upload_status="pending",
    )
    db.add(image)
    db.flush()
    image.storage_key = storage.storage_key(observation.id, image.id)
    descriptor = storage.upload_descriptor(
        observation_id=observation.id, image_id=image.id, key=image.storage_key
    )
    observation.status = "pending_upload"
    record_audit(
        db,
        action="image.upload_url_issued",
        actor=user,
        entity_type="image",
        entity_id=image.id,
        detail={"observation_id": observation.id, "mime": content_type},
    )
    return {"image_id": image.id, **descriptor}


def complete_upload(db: Session, *, user: User, observation: Observation, image_id: str) -> dict:
    image = db.get(ImageAsset, image_id)
    if image is None or image.observation_id != observation.id:
        raise ApiError(404, "not_found", "Image not found for this observation")
    if not storage.exists(image.storage_key):
        raise ApiError(409, "upload_incomplete", "Image bytes have not been uploaded")
    image.upload_status = "uploaded"
    observation.status = "uploaded"
    record_audit(
        db,
        action="image.uploaded",
        actor=user,
        entity_type="image",
        entity_id=image.id,
        detail={"observation_id": observation.id},
    )
    quality = assessment_service.run_quality_gate(db, image)
    prediction = assessment_service.run_assessment(
        db, observation=observation, image=image, quality=quality
    )
    return {
        "image_id": image.id,
        "observation_id": observation.id,
        "status": observation.status,
        "assessment_id": prediction.id,
    }


def request_review(
    db: Session, *, user: User, observation: Observation, reason: str | None
) -> ReviewRequest:
    existing = db.scalar(
        select(ReviewRequest).where(
            ReviewRequest.observation_id == observation.id,
            ReviewRequest.status == "open",
        )
    )
    if existing is not None:
        return existing
    request = ReviewRequest(
        observation_id=observation.id,
        requested_by=user.id,
        reason=reason[:300] if reason else None,
        status="open",
    )
    db.add(request)
    previous = observation.status
    observation.status = "pending_review"
    db.add(
        ReviewEvent(
            observation_id=observation.id,
            from_status=previous,
            to_status="pending_review",
            actor_id=user.id,
            reason=reason,
        )
    )
    verification = db.get(ObservationVerification, observation.id)
    if verification is None:
        db.add(
            ObservationVerification(
                observation_id=observation.id,
                status="pending_review",
                evidence_tier="unverified",
            )
        )
    else:
        verification.status = "pending_review"
    record_audit(
        db,
        action="review.requested",
        actor=user,
        entity_type="observation",
        entity_id=observation.id,
        reason=reason,
    )
    return request


def supported_targets(db: Session, crop_code: str) -> list[Target]:
    return db.scalars(
        select(Target).where(Target.crop_code == crop_code, Target.supported.is_(True))
    ).all()


def catalogue_entry(db: Session, crop: Crop) -> dict:
    targets = supported_targets(db, crop.code)
    return {
        "code": crop.code,
        "name": crop.name,
        "supported": crop.supported,
        "photo_assessment_available": bool(crop.supported and targets),
        "targets": [
            {
                "code": target.code,
                "name": target.name,
                "kind": target.kind,
                "forecast_eligible": target.forecast_eligible,
            }
            for target in targets
        ],
    }

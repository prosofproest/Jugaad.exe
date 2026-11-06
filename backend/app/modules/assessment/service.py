"""Quality gate and demo photo assessment.

No real image model is connected. The demo classifier is deterministic, returns
qualitative bands only, never a probability, and is labelled ``is_demo`` so a
client must render a demo badge. Abstention is a first-class outcome: a failed
quality gate or an unsupported crop/target never yields a forced class.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import (
    Crop,
    ImageAsset,
    ImagePrediction,
    ImageQualityResult,
    Observation,
    Target,
)
from app.modules.audit.service import record_audit


def _now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


def run_quality_gate(db: Session, image: ImageAsset) -> ImageQualityResult:
    settings = get_settings()
    flags: list[str] = []
    if image.original_width is None or image.original_height is None:
        flags.append("metadata_missing")
    else:
        if (
            image.original_width < settings.min_image_dimension
            or image.original_height < settings.min_image_dimension
        ):
            flags.append("low_resolution")
    if image.bytes is not None and image.bytes < 1024:
        flags.append("blur")
    if image.mime not in settings.allowed_image_types:
        flags.append("unsupported_type")

    result = "pass" if not flags else "fail"
    row = ImageQualityResult(
        image_id=image.id,
        gate_version=settings.quality_gate_version,
        result=result,
        flags=flags,
        thresholds={
            "min_dimension": settings.min_image_dimension,
            "max_upload_bytes": settings.max_upload_bytes,
            "min_bytes_demo_blur_heuristic": 1024,
        },
        is_demo=True,
    )
    db.add(row)
    record_audit(
        db,
        action="quality.evaluated",
        entity_type="image",
        entity_id=image.id,
        detail={"result": result, "flags": flags, "gate_version": row.gate_version},
    )
    return row


def _abstain(
    db: Session,
    *,
    observation: Observation,
    image: ImageAsset,
    reason: str,
    quality_flags: list[str],
) -> ImagePrediction:
    settings = get_settings()
    prediction = ImagePrediction(
        image_id=image.id,
        model_version=settings.image_model_version,
        candidates=[],
        confidence_band="not_calibrated",
        calibrated=False,
        abstained=True,
        abstain_reason=reason,
        quality_flags=quality_flags,
        is_demo=True,
        generated_at=_now(),
    )
    db.add(prediction)
    observation.status = "abstained"
    record_audit(
        db,
        action="assessment.abstained",
        entity_type="observation",
        entity_id=observation.id,
        detail={"reason": reason, "quality_flags": quality_flags},
    )
    return prediction


def run_assessment(
    db: Session,
    *,
    observation: Observation,
    image: ImageAsset,
    quality: ImageQualityResult,
) -> ImagePrediction:
    settings = get_settings()
    observation.status = "assessing"
    db.flush()

    if quality.result != "pass":
        return _abstain(
            db,
            observation=observation,
            image=image,
            reason="insufficient_quality",
            quality_flags=list(quality.flags),
        )

    crop = db.get(Crop, observation.crop_code)
    if crop is None or not crop.supported:
        return _abstain(
            db,
            observation=observation,
            image=image,
            reason="unsupported_crop",
            quality_flags=[],
        )

    targets = db.scalars(
        select(Target)
        .where(Target.crop_code == observation.crop_code, Target.supported.is_(True))
        .order_by(Target.code)
    ).all()
    if not targets:
        return _abstain(
            db,
            observation=observation,
            image=image,
            reason="unsupported_target",
            quality_flags=[],
        )

    # Deterministic demo candidates. Bands are qualitative; no probability is
    # emitted because calibration has not been approved.
    candidates = [
        {"label": target.code, "band": "medium" if index == 0 else "low"}
        for index, target in enumerate(targets[:3])
    ]
    prediction = ImagePrediction(
        image_id=image.id,
        model_version=settings.image_model_version,
        candidates=candidates,
        confidence_band="low",
        calibrated=False,
        abstained=False,
        abstain_reason=None,
        quality_flags=[],
        is_demo=True,
        generated_at=_now(),
    )
    db.add(prediction)
    observation.status = "assessed"
    record_audit(
        db,
        action="assessment.generated",
        entity_type="observation",
        entity_id=observation.id,
        detail={"model_version": prediction.model_version, "is_demo": True},
    )
    return prediction


def latest_prediction(db: Session, observation_id: str) -> ImagePrediction | None:
    return db.scalar(
        select(ImagePrediction)
        .join(ImageAsset, ImagePrediction.image_id == ImageAsset.id)
        .where(ImageAsset.observation_id == observation_id)
        .order_by(ImagePrediction.generated_at.desc())
    )


def latest_quality(db: Session, observation_id: str) -> ImageQualityResult | None:
    return db.scalar(
        select(ImageQualityResult)
        .join(ImageAsset, ImageQualityResult.image_id == ImageAsset.id)
        .where(ImageAsset.observation_id == observation_id)
        .order_by(ImageQualityResult.created_at.desc())
    )


def latest_image(db: Session, observation_id: str) -> ImageAsset | None:
    return db.scalar(
        select(ImageAsset)
        .where(ImageAsset.observation_id == observation_id)
        .order_by(ImageAsset.created_at.desc())
    )


def assessment_payload(db: Session, observation: Observation) -> dict:
    prediction = latest_prediction(db, observation.id)
    quality = latest_quality(db, observation.id)
    if prediction is None:
        return {
            "observation_id": observation.id,
            "state": observation.status if observation.status in {"pending_upload", "failed"} else "unavailable",
            "abstention_reason": None,
            "quality": None,
            "candidates": [],
            "confidence": {"band": "not_calibrated", "calibrated": False},
            "model_version": None,
            "generated_at": None,
            "is_demo": observation.is_demo,
            "notice": "Assistive photo assessment, not a diagnosis.",
        }
    return {
        "observation_id": observation.id,
        "state": "abstained" if prediction.abstained else "assessed",
        "abstention_reason": prediction.abstain_reason,
        "quality": (
            {"result": quality.result, "flags": list(quality.flags)} if quality else None
        ),
        "candidates": list(prediction.candidates),
        "confidence": {
            "band": prediction.confidence_band,
            "calibrated": prediction.calibrated,
            "probability": None,
        },
        "model_version": prediction.model_version,
        "generated_at": prediction.generated_at.isoformat(),
        "is_demo": prediction.is_demo,
        "notice": "Assistive photo assessment, not a diagnosis.",
    }

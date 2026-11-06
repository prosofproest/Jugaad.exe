"""Assessment routes (versioned inference contract).

This surface is the server-side half of the Phase 3 result card. It is mounted
even when no model is configured, so clients receive an explicit safe
``failed`` outcome instead of a 500.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Query

from app.core.config import get_settings
from app.modules.assessments.explanation import NOT_A_DIAGNOSIS
from app.modules.assessments.policy import PolicyError, load_policy_file
from app.modules.assessments.registry import RegistryError, load_registry_file
from app.modules.assessments.schemas import (
    AssessmentHistory,
    AssessmentRequest,
    AssessmentResponse,
)
from app.modules.assessments.service import AssessmentService
from app.modules.assessments.store import InMemoryPredictionStore

router = APIRouter(prefix="/assessments", tags=["assessments"])


class UnconfiguredAssessmentService:
    """Safe placeholder when no policy or registry path is configured."""

    def assess(self, request: AssessmentRequest) -> AssessmentResponse:
        return AssessmentResponse(
            assessment_id=None,
            state="failed",
            reason_code="triage_not_configured",
            reason_text=(
                "Photo assessment is not configured in this deployment. "
                f"{NOT_A_DIAGNOSIS} Request expert review if you need help."
            ),
            quality_flag=None,
            quality_flags=[],
            candidates=[],
            confidence_band=None,
            calibrated=False,
            calibration_version=None,
            model_version=request.model_version or "not_configured",
            taxonomy_version=None,
            quality_gate_version=None,
            decision_thresholds=None,
            ood_score=None,
            generated_at=datetime.now(UTC),
            is_demo=False,
            next_steps=["request_review"],
            not_a_diagnosis=True,
            supported_crops=None,
            error_code="triage_not_configured",
            retryable=False,
        )

    def get(self, prediction_id: str) -> AssessmentResponse | None:
        return None

    def history(self, *, limit: int = 20, cursor: str | None = None) -> AssessmentHistory:
        return AssessmentHistory(items=[], next_cursor=None)


ServiceLike = AssessmentService | UnconfiguredAssessmentService

_service: ServiceLike | None = None


def _build_default() -> ServiceLike:
    settings = get_settings()
    if not settings.assessment_policy_path or not settings.model_registry_path:
        return UnconfiguredAssessmentService()
    try:
        policy = load_policy_file(settings.assessment_policy_path)
        registry = load_registry_file(settings.model_registry_path)
    except (PolicyError, RegistryError):
        return UnconfiguredAssessmentService()
    return AssessmentService(
        policy=policy,
        registry=registry,
        store=InMemoryPredictionStore(),
        registry_base_dir=Path(settings.model_registry_path).resolve().parent,
    )


def get_assessment_service() -> ServiceLike:
    global _service
    if _service is None:
        _service = _build_default()
    return _service


def set_assessment_service(service: ServiceLike | None) -> None:
    """Test/DI hook. Passing ``None`` restores lazy default construction."""

    global _service
    _service = service


@router.post("", response_model=AssessmentResponse)
def create_assessment(
    payload: AssessmentRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1),
) -> AssessmentResponse:
    if idempotency_key != payload.client_assessment_id:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key must match client_assessment_id",
        )
    return get_assessment_service().assess(payload)


@router.get("", response_model=AssessmentHistory)
def list_assessments(
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> AssessmentHistory:
    try:
        return get_assessment_service().history(limit=limit, cursor=cursor)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{prediction_id}", response_model=AssessmentResponse)
def get_assessment(prediction_id: str) -> AssessmentResponse:
    response = get_assessment_service().get(prediction_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return response

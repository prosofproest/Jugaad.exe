"""Promotion workflow: trained -> evaluated -> approved -> serving.

The workflow is fail-closed. A synthetic fixture may reach ``evaluated`` and no
further. Approval requires non-demo provenance, an approved calibration
artefact, an explicit approval timestamp and human sign-off; none of those can
be inferred by this scaffold.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .backend import ensure_backend_on_path
from .evaluate import report_metrics
from .train import TrainedModel

PROMOTABLE_STATUSES = ("evaluated", "approved")


class PromotionError(ValueError):
    """Raised when a promotion request is not allowed."""


def _parse_timestamp(value: str, field: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise PromotionError(f"{field} must be an ISO-8601 timestamp") from error


def build_registry_entry(
    model: TrainedModel,
    report: dict[str, Any],
    *,
    artefact_path: str,
    requested_status: str = "evaluated",
    approved_at: str | None = None,
    calibration_version: str | None = None,
    calibration_approved: bool = False,
) -> Any:
    """Build and self-validate a registry entry for the promotion workflow."""

    ensure_backend_on_path()
    from app.modules.assessments.registry import ModelRegistry, RegistryEntry

    if requested_status not in PROMOTABLE_STATUSES:
        raise PromotionError(f"requested_status must be one of {PROMOTABLE_STATUSES}")
    if not artefact_path.strip():
        raise PromotionError("artefact_path is required")
    if report.get("model_checksum") != model.checksum:
        raise PromotionError("evaluation report does not match the model checksum")
    if report.get("training_data_fingerprint") != model.training_data_fingerprint:
        raise PromotionError("evaluation report does not match the training data")
    if report.get("model_version") != model.model_version:
        raise PromotionError("evaluation report does not match the model version")
    if model.metric_provenance == "synthetic_fixture" and not model.is_demo:
        raise PromotionError("synthetic metrics must keep is_demo=true")

    approval_time: datetime | None = None
    if requested_status == "approved":
        if model.is_demo or model.metric_provenance == "synthetic_fixture":
            raise PromotionError("synthetic_fixture_cannot_be_approved")
        if model.metric_provenance not in {"validation", "field_test"}:
            raise PromotionError("approval requires validation or field-test metrics")
        if approved_at is None:
            raise PromotionError("approval requires an explicit approved_at timestamp")
        if not calibration_approved or not calibration_version:
            raise PromotionError("approval requires an approved calibration artefact")
        approval_time = _parse_timestamp(approved_at, "approved_at")

    entry = RegistryEntry(
        model_version=model.model_version,
        status=requested_status,
        artefact_path=artefact_path,
        sha256=model.checksum,
        taxonomy_version=model.taxonomy_version,
        preprocessing_version=model.feature_contract_version,
        calibration_version=calibration_version,
        calibration_approved=calibration_approved,
        metrics=report_metrics(report),
        metric_provenance=model.metric_provenance,
        is_demo=model.is_demo,
        created_at=_parse_timestamp(model.trained_at, "trained_at"),
        approved_at=approval_time,
    )
    # Validate through the serving gate's own schema before returning.
    ModelRegistry(models=[entry])
    return entry


def registry_entry_json(entry: Any) -> dict[str, Any]:
    return entry.model_dump(mode="json")

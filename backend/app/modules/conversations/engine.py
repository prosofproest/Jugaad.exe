"""Pluggable assessment engine behind the chat reply.

The chat is a wrapper around the photo-assessment pipeline, not a free-form
diagnosis bot (spec 08 §1). This module defines the seam the real model plugs
into. Two implementations ship today:

* ``DemoAssessmentEngine`` — deterministic, visibly labelled synthetic output so
  the whole path can be exercised before a provider key and taxonomy exist. It
  still abstains on a failed quality gate and never invents an assessment for a
  missing image.
* ``UnavailableAssessmentEngine`` — fails closed with
  ``model_not_configured``. This is what a deployment gets if it selects an
  engine that is not implemented yet.

Adding a real provider means implementing ``AssessmentEngine.assess`` and
selecting it in ``get_assessment_engine``. The provider must return one of the
fixed label sets from the approved policy, never free-form advice.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol

from app.core.config import get_settings
from app.modules.conversations.models import AssessmentState

DEMO_MODEL_VERSION = "demo-chat-0.1"
UNAVAILABLE_MODEL_VERSION = "unconfigured-0.0"

# Synthetic labels only. They are not a crop/target taxonomy and must never be
# read as a diagnosis. The UI renders the demo badge from ``is_demo``.
_DEMO_LABELS: tuple[tuple[str, str], ...] = (
    ("demo_pattern_a", "Demo pattern A (synthetic)"),
    ("demo_pattern_b", "Demo pattern B (synthetic)"),
    ("demo_healthy_like", "Demo healthy-like (synthetic)"),
)

_QUALITY_REASON: dict[str, str] = {
    "blurry": "The photo is too blurry to assess. Hold the camera steady and retake.",
    "dark": "The photo is too dark to assess. Move to better light and retake.",
    "overexposed": "The photo is too bright or has blown highlights. Retake in softer light.",
    "low_resolution": "The photo is too small to assess. Retake at a higher resolution.",
    "no_plant": "No plant was detected in the photo. Frame the affected leaves and retake.",
}


@dataclass(frozen=True)
class UploadContext:
    """The parts of a stored upload the engine is allowed to see."""

    upload_id: str
    sha256: str
    width: int
    height: int
    quality_result: str
    quality_flags: tuple[str, ...]


@dataclass(frozen=True)
class EngineResult:
    state: AssessmentState
    reason_text: str
    model_version: str
    is_demo: bool
    reason_code: str | None = None
    quality_flag: str | None = None
    quality_flags: list[str] = field(default_factory=list)
    candidates: list[dict] = field(default_factory=list)
    confidence_band: str | None = None
    calibrated: bool = False
    next_steps: list[str] = field(default_factory=list)
    error_code: str | None = None
    retryable: bool = False


class AssessmentEngine(Protocol):
    """The boundary a real provider implements."""

    model_version: str
    is_demo: bool

    def assess(
        self,
        *,
        upload: UploadContext | None,
        crop_id: str | None = None,
        context: str | None = None,
    ) -> EngineResult: ...


def _demo_candidates(sha256: str) -> list[dict]:
    """Deterministic candidates from the image hash (same image, same reply)."""

    digest = hashlib.sha256(sha256.encode("utf-8")).digest()
    raw = [digest[0], digest[1], digest[2]]
    total = sum(raw) or 1
    ordered = sorted(
        zip(_DEMO_LABELS, raw, strict=True),
        key=lambda item: item[1],
        reverse=True,
    )
    return [
        {
            "label": label,
            "display_name": display_name,
            "score": round(value / total, 4),
        }
        for (label, display_name), value in ordered
    ]


class DemoAssessmentEngine:
    """Labelled synthetic engine used until a real provider is connected."""

    model_version = DEMO_MODEL_VERSION
    is_demo = True

    def assess(
        self,
        *,
        upload: UploadContext | None,
        crop_id: str | None = None,
        context: str | None = None,
    ) -> EngineResult:
        del crop_id, context  # No crop taxonomy exists yet; never infer one.

        if upload is None:
            return EngineResult(
                state="abstained",
                reason_code="no_image",
                reason_text="No photo was attached, so there is nothing to assess.",
                model_version=self.model_version,
                is_demo=True,
                next_steps=[],
            )

        if upload.quality_result != "pass":
            flag = upload.quality_result
            return EngineResult(
                state="abstained",
                reason_code="quality_gate_failed",
                reason_text=_QUALITY_REASON.get(
                    flag, "The photo did not pass the image-quality check. Retake it."
                ),
                quality_flag=flag,
                quality_flags=list(upload.quality_flags),
                model_version=self.model_version,
                is_demo=True,
                next_steps=["retake"],
            )

        return EngineResult(
            state="assessed",
            reason_text=(
                "Demo assessment from a synthetic classifier. This is an assistive "
                "visual result, not a diagnosis; no real model is connected yet."
            ),
            candidates=_demo_candidates(upload.sha256),
            confidence_band="not_calibrated",
            calibrated=False,
            model_version=self.model_version,
            is_demo=True,
            next_steps=["add_context", "request_review"],
        )


class UnavailableAssessmentEngine:
    """Fail closed when a deployment selects an engine that is not wired."""

    model_version = UNAVAILABLE_MODEL_VERSION
    is_demo = False

    def assess(
        self,
        *,
        upload: UploadContext | None,
        crop_id: str | None = None,
        context: str | None = None,
    ) -> EngineResult:
        del upload, crop_id, context
        return EngineResult(
            state="failed",
            reason_code="model_not_configured",
            reason_text=(
                "No assessment model is configured for this deployment. "
                "The photo was stored; no result was invented."
            ),
            model_version=self.model_version,
            is_demo=False,
            next_steps=["retry"],
            error_code="model_not_configured",
            retryable=False,
        )


@lru_cache
def get_assessment_engine() -> AssessmentEngine:
    """Select the engine from settings. Unknown values fail closed."""

    name = get_settings().chat_engine.strip().lower()
    if name in {"demo", "synthetic"}:
        return DemoAssessmentEngine()
    return UnavailableAssessmentEngine()

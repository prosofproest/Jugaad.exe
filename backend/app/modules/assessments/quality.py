"""Server-side image quality gate.

Metric extraction (blur, exposure, plant presence) happens upstream from a
versioned preprocessing recipe. This module applies the versioned thresholds
and returns a documented reason code. All metrics are required: a missing
metric fails closed rather than silently passing the image.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.assessments.policy import QualityThresholds

QualityResult = Literal[
    "pass",
    "blurry",
    "dark",
    "overexposed",
    "low_resolution",
    "no_plant",
]

# Deterministic precedence for the single user-facing reason.
_PRECEDENCE: tuple[QualityResult, ...] = (
    "low_resolution",
    "dark",
    "overexposed",
    "blurry",
    "no_plant",
)


class ImageMetrics(BaseModel):
    """Metrics produced by the versioned quality-metric extractor."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    width: int = Field(gt=0)
    height: int = Field(gt=0)
    laplacian_variance: float = Field(ge=0)
    mean_luma: float = Field(ge=0, le=255)
    clipped_fraction: float = Field(ge=0, le=1)
    plant_presence: float = Field(ge=0, le=1)


@dataclass(frozen=True)
class QualityOutcome:
    result: QualityResult
    flags: tuple[QualityResult, ...]
    gate_version: str
    thresholds: dict[str, float | int]

    @property
    def passed(self) -> bool:
        return self.result == "pass"


def evaluate_quality(metrics: ImageMetrics, thresholds: QualityThresholds) -> QualityOutcome:
    """Apply the configured gate. Every failing metric is retained as a flag."""

    flags: list[QualityResult] = []

    if metrics.width < thresholds.min_width or metrics.height < thresholds.min_height:
        flags.append("low_resolution")
    if metrics.mean_luma < thresholds.min_mean_luma:
        flags.append("dark")
    if metrics.mean_luma > thresholds.max_mean_luma or (
        metrics.clipped_fraction > thresholds.max_clipped_fraction
    ):
        flags.append("overexposed")
    if metrics.laplacian_variance < thresholds.min_laplacian_variance:
        flags.append("blurry")
    if metrics.plant_presence < thresholds.min_plant_presence:
        flags.append("no_plant")

    ordered = tuple(flag for flag in _PRECEDENCE if flag in flags)
    primary: QualityResult = ordered[0] if ordered else "pass"

    return QualityOutcome(
        result=primary,
        flags=ordered,
        gate_version=thresholds.version,
        thresholds=thresholds.model_dump(),
    )

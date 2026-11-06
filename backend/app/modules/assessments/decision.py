"""D8 abstention decision function.

Applied only after the server quality gate passes and after the crop check.
Any breach returns an explicit reason code and no candidate list; the model
never maps an unknown image onto the nearest supported class.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from app.modules.assessments.policy import TriagePolicy

ReasonCode = Literal[
    "below_class_threshold",
    "low_margin",
    "high_entropy",
    "out_of_distribution",
    "unsupported_crop",
    "quality_gate_failed",
]

ConfidenceBand = Literal["low", "medium", "high", "not_calibrated"]


class DecisionError(ValueError):
    """Raised when scores cannot be evaluated safely."""


@dataclass(frozen=True)
class Candidate:
    label: str
    display_name: str
    score: float


@dataclass(frozen=True)
class Decision:
    state: Literal["assessed", "abstained"]
    reason_code: ReasonCode | None
    candidates: tuple[Candidate, ...]
    confidence_band: ConfidenceBand | None
    top1_label: str | None
    top1_score: float | None
    margin: float
    entropy: float
    ood_score: float
    calibrated: bool

    @property
    def abstained(self) -> bool:
        return self.state == "abstained"


def normalised_entropy(scores: Mapping[str, float]) -> float:
    """Shannon entropy divided by ``log(n)`` so it is comparable across class sets."""

    values = list(scores.values())
    if len(values) < 2:
        raise DecisionError("at least two classes are required")
    entropy = -sum(value * math.log(value) for value in values if value > 0)
    return entropy / math.log(len(values))


def decide(
    scores: Mapping[str, float],
    *,
    ood_score: float | None,
    calibrated: bool,
    policy: TriagePolicy,
) -> Decision:
    """Apply ``tau_c``, margin, entropy and OOD gates, in that safety order."""

    expected = set(policy.labels)
    provided = set(scores)
    if expected != provided:
        missing = sorted(expected - provided)
        extra = sorted(provided - expected)
        raise DecisionError(f"score labels mismatch; missing={missing} extra={extra}")

    for label, value in scores.items():
        if not math.isfinite(value):
            raise DecisionError(f"score for {label} must be finite")
        if value < 0.0 or value > 1.0:
            raise DecisionError(f"score for {label} must be in [0, 1]")

    total = sum(scores.values())
    if abs(total - 1.0) > 1e-6:
        raise DecisionError("class scores must sum to 1")

    if policy.decision.ood_enabled:
        if ood_score is None or not math.isfinite(ood_score):
            raise DecisionError("an OOD score is required when the OOD gate is enabled")
        if ood_score < 0.0 or ood_score > 1.0:
            raise DecisionError("OOD score must be in [0, 1]")

    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    top1_label, top1_score = ordered[0]
    second_score = ordered[1][1]
    margin = top1_score - second_score
    entropy = normalised_entropy(scores)

    tau_c = policy.class_definition(top1_label).tau_c
    ood_value = ood_score if ood_score is not None else 0.0

    reason: ReasonCode | None = None
    if policy.decision.ood_enabled and ood_value > policy.decision.ood_max:
        reason = "out_of_distribution"
    elif top1_score < tau_c:
        reason = "below_class_threshold"
    elif margin < policy.decision.margin:
        reason = "low_margin"
    elif entropy > policy.decision.entropy:
        reason = "high_entropy"

    if reason is not None:
        return Decision(
            state="abstained",
            reason_code=reason,
            candidates=(),
            confidence_band=None,
            top1_label=top1_label,
            top1_score=top1_score,
            margin=margin,
            entropy=entropy,
            ood_score=ood_value,
            calibrated=calibrated,
        )

    candidates = tuple(
        Candidate(
            label=label,
            display_name=policy.class_definition(label).display_name,
            score=score,
        )
        for label, score in ordered[: policy.max_candidates]
    )

    if not calibrated:
        band: ConfidenceBand = "not_calibrated"
    else:
        if policy.confidence_bands is None:
            raise DecisionError("calibrated decisions require confidence band thresholds")
        if top1_score >= policy.confidence_bands.high_min:
            band = "high"
        elif top1_score >= policy.confidence_bands.medium_min:
            band = "medium"
        else:
            band = "low"

    return Decision(
        state="assessed",
        reason_code=None,
        candidates=candidates,
        confidence_band=band,
        top1_label=top1_label,
        top1_score=top1_score,
        margin=margin,
        entropy=entropy,
        ood_score=ood_value,
        calibrated=calibrated,
    )

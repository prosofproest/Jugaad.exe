"""Out-of-distribution scoring and threshold fitting (D8).

A supervised ``unknown`` class is not open-set detection. This module supplies
an explicit bounded OOD score, a threshold fitted on held-out classes at a
declared false-accept rate, and the two gate metrics: unknown-vs-known AUROC
and false-accept rate at the shipped threshold.

The functions operate on an explicitly supplied set. They never invent a
threshold or a result.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from app.modules.assessments.calibration import CalibrationError, softmax


@dataclass(frozen=True)
class OODReport:
    threshold: float
    false_accept_rate: float
    detection_rate: float
    auroc: float
    n_known: int
    n_unknown: int


def ood_score_from_logits(logits: Sequence[float]) -> float:
    """Bounded OOD score: ``1 - max softmax``.

    Deployments may supply a different bounded score (for example a calibrated
    energy score) through the inference adapter; the decision function only
    requires a value in ``[0, 1]`` where higher means further from the
    validated domain.
    """

    return 1.0 - max(softmax(logits))


def fit_ood_threshold(
    known_scores: Sequence[float],
    *,
    max_false_accept_rate: float,
) -> float:
    """Set the threshold so at most ``max_false_accept_rate`` of knowns exceed it.

    ``max_false_accept_rate`` is a pre-registered D8 floor, supplied by the
    deployment. It is never defaulted.
    """

    if not known_scores:
        raise CalibrationError("at least one known score is required")
    if not 0.0 <= max_false_accept_rate < 1.0:
        raise CalibrationError("max_false_accept_rate must be in [0, 1)")
    for score in known_scores:
        if not math.isfinite(score) or score < 0.0 or score > 1.0:
            raise CalibrationError("OOD scores must be finite and in [0, 1]")

    ordered = sorted(known_scores)
    allowed = math.floor(max_false_accept_rate * len(ordered) + 1e-12)
    index = len(ordered) - allowed - 1
    # With a very small panel and a strict rate, allow zero false accepts.
    return float(ordered[max(index, 0)])


def _auroc(known_scores: Sequence[float], unknown_scores: Sequence[float]) -> float:
    if not known_scores or not unknown_scores:
        raise CalibrationError("both known and unknown scores are required")
    wins = 0.0
    for known in known_scores:
        for unknown in unknown_scores:
            if unknown > known:
                wins += 1.0
            elif unknown == known:
                wins += 0.5
    return wins / (len(known_scores) * len(unknown_scores))


def evaluate_ood(
    known_scores: Sequence[float],
    unknown_scores: Sequence[float],
    *,
    threshold: float,
) -> OODReport:
    """Report the gate metrics at a supplied threshold."""

    if not known_scores or not unknown_scores:
        raise CalibrationError("both known and unknown scores are required")
    for score in [*known_scores, *unknown_scores]:
        if not math.isfinite(score) or score < 0.0 or score > 1.0:
            raise CalibrationError("OOD scores must be finite and in [0, 1]")
    if not 0.0 <= threshold <= 1.0:
        raise CalibrationError("threshold must be in [0, 1]")

    false_accepts = sum(1 for score in known_scores if score > threshold)
    detections = sum(1 for score in unknown_scores if score > threshold)

    return OODReport(
        threshold=threshold,
        false_accept_rate=false_accepts / len(known_scores),
        detection_rate=detections / len(unknown_scores),
        auroc=_auroc(known_scores, unknown_scores),
        n_known=len(known_scores),
        n_unknown=len(unknown_scores),
    )

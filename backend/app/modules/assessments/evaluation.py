"""Evaluation harness for the image triage pipeline (Phase 3 §6.5).

The harness computes the Gate 3 report from an explicitly supplied, labelled
set: per-class precision/recall, macro F1, confusion matrix, top-k accuracy,
abstention rate and (only when calibration is approved) calibration
diagnostics.

Metrics are computed on **assessed** images and the abstention rate is reported
beside them, so performance is always reported at the shipped threshold. This
module never labels a sample, fabricates a split, or treats an abstention as a
correct prediction.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.modules.assessments.calibration import (
    CalibrationDiagnostics,
    CalibrationError,
    calibration_diagnostics,
)


@dataclass(frozen=True)
class EvaluationSample:
    true_label: str
    probabilities: Mapping[str, float]
    assessed: bool


@dataclass(frozen=True)
class PerClassMetrics:
    support: int
    precision: float
    recall: float
    f1: float


@dataclass(frozen=True)
class ClassificationReport:
    n_total: int
    n_assessed: int
    n_abstained: int
    abstention_rate: float
    per_class: dict[str, PerClassMetrics]
    macro_f1: float
    confusion: dict[str, dict[str, int]]
    top_k_accuracy: dict[int, float]
    calibration: CalibrationDiagnostics | None


def _validate_sample(sample: EvaluationSample, class_labels: Sequence[str]) -> None:
    if sample.true_label not in class_labels:
        raise CalibrationError(f"unknown true label: {sample.true_label}")
    if set(sample.probabilities) != set(class_labels):
        raise CalibrationError("probabilities must cover exactly the class set")
    total = sum(sample.probabilities.values())
    if abs(total - 1.0) > 1e-6:
        raise CalibrationError("probabilities must sum to 1")
    if any(value < 0.0 or value > 1.0 for value in sample.probabilities.values()):
        raise CalibrationError("probabilities must be in [0, 1]")


def evaluate_classifier(
    samples: Sequence[EvaluationSample],
    class_labels: Sequence[str],
    *,
    calibration_approved: bool,
    top_k: Sequence[int] = (1, 3),
    calibration_bins: int = 10,
) -> ClassificationReport:
    """Compute the report. Metrics are never produced without samples."""

    if not samples:
        raise CalibrationError("at least one evaluation sample is required")
    if len(set(class_labels)) != len(class_labels):
        raise CalibrationError("class labels must be unique")
    if not class_labels:
        raise CalibrationError("at least one class label is required")
    for sample in samples:
        _validate_sample(sample, class_labels)

    assessed = [sample for sample in samples if sample.assessed]
    n_total = len(samples)
    n_assessed = len(assessed)
    n_abstained = n_total - n_assessed

    labels = list(class_labels)
    true_positive = {label: 0 for label in labels}
    predicted_positive = {label: 0 for label in labels}
    support = {label: 0 for label in labels}
    confusion = {truth: {predicted: 0 for predicted in labels} for truth in labels}

    predictions: list[str] = []
    for sample in assessed:
        predicted = max(labels, key=lambda label: sample.probabilities[label])
        predictions.append(predicted)
        support[sample.true_label] += 1
        predicted_positive[predicted] += 1
        confusion[sample.true_label][predicted] += 1
        if predicted == sample.true_label:
            true_positive[sample.true_label] += 1

    per_class: dict[str, PerClassMetrics] = {}
    for label in labels:
        tp = true_positive[label]
        precision = tp / predicted_positive[label] if predicted_positive[label] else 0.0
        recall = tp / support[label] if support[label] else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        per_class[label] = PerClassMetrics(
            support=support[label],
            precision=precision,
            recall=recall,
            f1=f1,
        )

    represented = [metrics for metrics in per_class.values() if metrics.support > 0]
    macro_f1 = sum(metrics.f1 for metrics in represented) / len(represented) if represented else 0.0

    max_k = min(max(top_k, default=1), len(labels))
    top_k_accuracy: dict[int, float] = {}
    for k in sorted({value for value in top_k if 1 <= value <= max_k}):
        if not assessed:
            top_k_accuracy[k] = 0.0
            continue
        hits = 0
        for sample in assessed:
            ranking = sorted(labels, key=lambda label: sample.probabilities[label], reverse=True)[
                :k
            ]
            if sample.true_label in ranking:
                hits += 1
        top_k_accuracy[k] = hits / len(assessed)

    calibration: CalibrationDiagnostics | None = None
    if calibration_approved:
        if not assessed:
            raise CalibrationError("calibration metrics require assessed samples")
        calibration = calibration_diagnostics(
            [[sample.probabilities[label] for label in labels] for sample in assessed],
            [labels.index(sample.true_label) for sample in assessed],
            n_bins=calibration_bins,
        )

    return ClassificationReport(
        n_total=n_total,
        n_assessed=n_assessed,
        n_abstained=n_abstained,
        abstention_rate=n_abstained / n_total,
        per_class=per_class,
        macro_f1=macro_f1,
        confusion=confusion,
        top_k_accuracy=top_k_accuracy,
        calibration=calibration,
    )

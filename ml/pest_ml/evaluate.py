"""Evaluation wrapper around the backend's Gate 3 harness.

The scaffold reuses ``app.modules.assessments.evaluation`` so training and
serving are judged by the same report. Calibration diagnostics stay disabled
unless an operator supplies an approved calibration artefact; the synthetic
fixture has none, so the report is explicitly a fixture diagnostic.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict
from typing import Any

from .backend import ensure_backend_on_path
from .manifest import DatasetItem, DatasetManifest
from .train import TrainedModel


class EvaluationError(ValueError):
    """Raised when an evaluation cannot be produced honestly."""


def evaluate_model(
    model: TrainedModel,
    items: Sequence[DatasetItem],
    manifest: DatasetManifest,
    *,
    split_name: str = "test",
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    """Evaluate on an explicitly supplied split and return a JSON-safe report."""

    if not items:
        raise EvaluationError("evaluation split is empty")

    ensure_backend_on_path()
    from app.modules.assessments.evaluation import (
        EvaluationSample,
        evaluate_classifier,
    )

    labels = list(model.classes)
    samples = [
        EvaluationSample(
            true_label=item.label,
            probabilities=model.predict(item.features),
            assessed=True,
        )
        for item in items
    ]
    report = evaluate_classifier(
        samples,
        labels,
        calibration_approved=False,
        top_k=(1, 2),
    )

    metrics = {
        "macro_f1": round(report.macro_f1, 12),
        "top1_accuracy": round(report.top_k_accuracy.get(1, 0.0), 12),
        "abstention_rate": round(report.abstention_rate, 12),
    }
    return {
        "schema_version": "1.0",
        "split": split_name,
        "is_demo": model.is_demo,
        "metric_provenance": model.metric_provenance,
        "model_version": model.model_version,
        "model_checksum": model.checksum,
        "training_data_fingerprint": model.training_data_fingerprint,
        "dataset_id": manifest.dataset_id,
        "data_fingerprint": manifest.data_fingerprint,
        "n_total": report.n_total,
        "n_assessed": report.n_assessed,
        "n_abstained": report.n_abstained,
        "abstention_rate": round(report.abstention_rate, 12),
        "macro_f1": round(report.macro_f1, 12),
        "top_k_accuracy": {
            str(key): round(value, 12) for key, value in report.top_k_accuracy.items()
        },
        "per_class": {
            label: asdict(metrics_entry) for label, metrics_entry in report.per_class.items()
        },
        "confusion": report.confusion,
        "calibration": None,
        "metrics": metrics,
        "evaluated_at": evaluated_at or model.trained_at,
    }


def report_metrics(report: dict[str, Any]) -> dict[str, float]:
    metrics = report.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        raise EvaluationError("evaluation report has no metrics")
    return {str(key): float(value) for key, value in metrics.items()}

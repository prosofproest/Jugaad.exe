"""Deterministic training harness for the synthetic scaffold.

The baseline is a nearest-centroid classifier over pre-extracted feature
vectors. It exists to prove the pipeline is wired end to end: manifest in,
split, fit, checksum, evaluation report out. It is **not** an image model, and
its metrics are fixture diagnostics, never a performance claim.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .features import validate_feature_vector
from .manifest import DatasetItem, DatasetManifest, canonical_json_bytes

MODEL_FAMILY = "synthetic-nearest-centroid"
ARTEFACT_SCHEMA_VERSION = "1.0"


class TrainingError(ValueError):
    """Raised when training cannot produce a trustworthy artefact."""


def _softmax(logits: Sequence[float]) -> list[float]:
    if not logits:
        raise TrainingError("logits must not be empty")
    peak = max(logits)
    exps = [math.exp(value - peak) for value in logits]
    total = sum(exps)
    return [value / total for value in exps]


def _training_fingerprint(items: Sequence[DatasetItem]) -> str:
    canonical = [
        {
            "image_id": item.image_id,
            "label": item.label,
            "features": list(item.features),
        }
        for item in sorted(items, key=lambda entry: entry.image_id)
    ]
    return hashlib.sha256(canonical_json_bytes(canonical)).hexdigest()


@dataclass(frozen=True)
class TrainedModel:
    model_version: str
    classes: tuple[str, ...]
    centroids: dict[str, tuple[float, ...]]
    scale: float
    feature_dim: int
    feature_contract_version: str
    taxonomy_version: str
    is_demo: bool
    metric_provenance: str
    training_data_fingerprint: str
    trained_at: str
    checksum: str

    def payload(self) -> dict[str, Any]:
        return {
            "schema_version": ARTEFACT_SCHEMA_VERSION,
            "model_family": MODEL_FAMILY,
            "model_version": self.model_version,
            "classes": list(self.classes),
            "centroids": {label: list(values) for label, values in self.centroids.items()},
            "scale": self.scale,
            "feature_dim": self.feature_dim,
            "feature_contract_version": self.feature_contract_version,
            "taxonomy_version": self.taxonomy_version,
            "is_demo": self.is_demo,
            "metric_provenance": self.metric_provenance,
            "training_data_fingerprint": self.training_data_fingerprint,
            "trained_at": self.trained_at,
        }

    def predict(self, features: Sequence[object]) -> dict[str, float]:
        vector = validate_feature_vector(
            features,
            expected_dim=self.feature_dim,
            context="prediction features",
        )
        logits: list[float] = []
        for label in self.classes:
            centroid = self.centroids[label]
            squared_distance = sum(
                (value - reference) ** 2 for value, reference in zip(vector, centroid, strict=True)
            )
            logits.append(-0.5 * squared_distance / self.scale)
        return dict(zip(self.classes, _softmax(logits), strict=True))


def artefact_bytes(model: TrainedModel) -> bytes:
    return canonical_json_bytes(model.payload())


def save_artefact(model: TrainedModel, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = artefact_bytes(model)
    actual = hashlib.sha256(payload).hexdigest()
    if actual != model.checksum:
        raise TrainingError("artefact checksum does not match the model")
    destination.write_bytes(payload)
    return destination


def load_artefact(path: str | Path) -> TrainedModel:
    payload = Path(path).read_bytes()
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as error:
        raise TrainingError("model artefact is not valid JSON") from error
    if not isinstance(raw, dict):
        raise TrainingError("model artefact must be a JSON object")
    checksum = hashlib.sha256(payload).hexdigest()
    try:
        model = TrainedModel(
            model_version=raw["model_version"],
            classes=tuple(raw["classes"]),
            centroids={
                label: tuple(float(value) for value in values)
                for label, values in raw["centroids"].items()
            },
            scale=float(raw["scale"]),
            feature_dim=int(raw["feature_dim"]),
            feature_contract_version=raw["feature_contract_version"],
            taxonomy_version=raw["taxonomy_version"],
            is_demo=bool(raw["is_demo"]),
            metric_provenance=raw["metric_provenance"],
            training_data_fingerprint=raw["training_data_fingerprint"],
            trained_at=raw["trained_at"],
            checksum=checksum,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise TrainingError("model artefact is missing required fields") from error
    if artefact_bytes(model) != payload:
        raise TrainingError("model artefact is not canonical")
    return model


def train_model(
    items: Sequence[DatasetItem],
    manifest: DatasetManifest,
    *,
    model_version: str,
    trained_at: str | None = None,
) -> TrainedModel:
    """Fit the deterministic baseline on an explicitly supplied training split."""

    if not items:
        raise TrainingError("training split is empty")
    if not model_version.strip():
        raise TrainingError("model_version must be a non-empty string")

    classes = manifest.class_labels
    grouped: dict[str, list[DatasetItem]] = {label: [] for label in classes}
    for item in items:
        if item.label not in grouped:
            raise TrainingError(f"training item has unknown label: {item.label}")
        grouped[item.label].append(item)
    missing = [label for label, members in grouped.items() if not members]
    if missing:
        raise TrainingError(f"training split is missing classes: {', '.join(missing)}")

    centroids: dict[str, tuple[float, ...]] = {}
    for label, members in grouped.items():
        dimensions = len(members[0].features)
        centroids[label] = tuple(
            sum(member.features[index] for member in members) / len(members)
            for index in range(dimensions)
        )

    within_class: list[float] = []
    for item in items:
        centroid = centroids[item.label]
        within_class.append(
            sum(
                (value - reference) ** 2
                for value, reference in zip(item.features, centroid, strict=True)
            )
        )
    scale = max(sum(within_class) / len(within_class), 1e-6)

    fingerprint = _training_fingerprint(items)
    provisional = TrainedModel(
        model_version=model_version,
        classes=classes,
        centroids=centroids,
        scale=scale,
        feature_dim=manifest.feature_dim,
        feature_contract_version=manifest.feature_contract_version,
        taxonomy_version=manifest.taxonomy_version,
        is_demo=manifest.is_demo,
        metric_provenance="synthetic_fixture" if manifest.is_demo else "validation",
        training_data_fingerprint=fingerprint,
        trained_at=trained_at or manifest.created_at,
        checksum="",
    )
    checksum = hashlib.sha256(artefact_bytes(provisional)).hexdigest()
    return TrainedModel(
        model_version=provisional.model_version,
        classes=provisional.classes,
        centroids=provisional.centroids,
        scale=provisional.scale,
        feature_dim=provisional.feature_dim,
        feature_contract_version=provisional.feature_contract_version,
        taxonomy_version=provisional.taxonomy_version,
        is_demo=provisional.is_demo,
        metric_provenance=provisional.metric_provenance,
        training_data_fingerprint=provisional.training_data_fingerprint,
        trained_at=provisional.trained_at,
        checksum=checksum,
    )

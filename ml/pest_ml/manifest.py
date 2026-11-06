"""Dataset-manifest loading and validation.

A manifest is the only way training data enters the scaffold. It records the
fixture kind, licence, provenance, taxonomy, feature contract and checksum of
the data file, and it refuses to load a field dataset that lacks documented
permissions. Synthetic fixtures are always marked ``is_demo`` and can never be
promoted to serving.

The matching JSON Schema is ``ml/contract/dataset-manifest.schema.json``.
Validation is implemented here without a third-party JSON Schema dependency.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .features import validate_feature_vector

REQUIRED_KEYS = (
    "schema_version",
    "dataset_id",
    "description",
    "fixture_kind",
    "is_demo",
    "created_at",
    "licence",
    "provenance",
    "feature_contract_version",
    "feature_dim",
    "taxonomy_version",
    "classes",
    "data_file",
    "data_sha256",
)

SYNTHETIC_KIND = "synthetic_fixture"
FIELD_KIND = "field_dataset"
UNUSABLE_LICENCES = {"", "unknown", "tbd", "todo", "none"}


class ManifestError(ValueError):
    """Raised when a dataset manifest cannot be trusted."""


@dataclass(frozen=True)
class DatasetClass:
    label: str
    display_name: str


@dataclass(frozen=True)
class DatasetItem:
    image_id: str
    group_id: str
    label: str
    features: tuple[float, ...]
    is_demo: bool
    synthetic: bool


@dataclass(frozen=True)
class DatasetManifest:
    path: Path
    dataset_id: str
    description: str
    fixture_kind: str
    is_demo: bool
    created_at: str
    licence: str
    provenance: str
    feature_contract_version: str
    feature_dim: int
    taxonomy_version: str
    classes: tuple[DatasetClass, ...]
    items: tuple[DatasetItem, ...]
    data_sha256: str
    data_fingerprint: str

    @property
    def class_labels(self) -> tuple[str, ...]:
        return tuple(entry.label for entry in self.classes)


def canonical_json_bytes(value: Any) -> bytes:
    """Stable, whitespace-free JSON used for fingerprints and checksums."""

    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _require_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"manifest field '{key}' must be a non-empty string")
    return value.strip()


def _require_bool(raw: dict[str, Any], key: str) -> bool:
    value = raw.get(key)
    if not isinstance(value, bool):
        raise ManifestError(f"manifest field '{key}' must be a boolean")
    return value


def _require_int(raw: dict[str, Any], key: str) -> int:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ManifestError(f"manifest field '{key}' must be a positive integer")
    return value


def _validate_fixture_kind(raw: dict[str, Any]) -> str:
    fixture_kind = _require_string(raw, "fixture_kind")
    is_demo = _require_bool(raw, "is_demo")
    licence = _require_string(raw, "licence")

    if fixture_kind == SYNTHETIC_KIND:
        if not is_demo:
            raise ManifestError("synthetic fixtures must set is_demo=true")
    elif fixture_kind == FIELD_KIND:
        if is_demo:
            raise ManifestError("field datasets must set is_demo=false")
        if licence.lower() in UNUSABLE_LICENCES:
            raise ManifestError("field datasets require a documented licence")
        permissions = raw.get("permissions")
        if not isinstance(permissions, dict):
            raise ManifestError("field datasets require a permissions object")
        for key in ("consent_ref", "ethics_ref", "data_owner"):
            value = permissions.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ManifestError(f"field datasets require permissions.{key}")
        if raw.get("personal_data") is True:
            privacy_ref = permissions.get("privacy_review_ref")
            if not isinstance(privacy_ref, str) or not privacy_ref.strip():
                raise ManifestError("personal_data datasets require permissions.privacy_review_ref")
    else:
        raise ManifestError(f"fixture_kind must be '{SYNTHETIC_KIND}' or '{FIELD_KIND}'")
    return fixture_kind


def _load_classes(raw: dict[str, Any]) -> tuple[DatasetClass, ...]:
    entries = raw.get("classes")
    if not isinstance(entries, list) or len(entries) < 2:
        raise ManifestError("classes must be a list with at least two entries")

    classes: list[DatasetClass] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ManifestError(f"classes[{index}] must be an object")
        label = entry.get("label")
        display_name = entry.get("display_name")
        if not isinstance(label, str) or not label.strip():
            raise ManifestError(f"classes[{index}].label must be a non-empty string")
        if not isinstance(display_name, str) or not display_name.strip():
            raise ManifestError(f"classes[{index}].display_name must be a non-empty string")
        if label in seen:
            raise ManifestError(f"duplicate class label: {label}")
        seen.add(label)
        classes.append(DatasetClass(label=label, display_name=display_name))
    return tuple(classes)


def _load_items(
    data_path: Path,
    *,
    fixture_kind: str,
    class_labels: set[str],
    feature_dim: int,
) -> tuple[DatasetItem, ...]:
    try:
        text = data_path.read_text(encoding="utf-8")
    except OSError as error:
        raise ManifestError(f"dataset file unreadable: {data_path}") from error

    items: list[DatasetItem] = []
    seen_ids: set[str] = set()
    group_labels: dict[str, str] = {}

    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ManifestError(f"invalid JSON on line {line_number}") from error
        if not isinstance(record, dict):
            raise ManifestError(f"line {line_number} must be a JSON object")

        for key in ("image_id", "group_id", "label", "features", "is_demo", "synthetic"):
            if key not in record:
                raise ManifestError(f"line {line_number} is missing '{key}'")

        image_id = record["image_id"]
        group_id = record["group_id"]
        label = record["label"]
        if not isinstance(image_id, str) or not image_id:
            raise ManifestError(f"line {line_number}: image_id must be a string")
        if not isinstance(group_id, str) or not group_id:
            raise ManifestError(f"line {line_number}: group_id must be a string")
        if not isinstance(label, str) or label not in class_labels:
            raise ManifestError(f"line {line_number}: unknown label '{label}'")
        if image_id in seen_ids:
            raise ManifestError(f"duplicate image_id: {image_id}")
        seen_ids.add(image_id)

        is_demo = record["is_demo"]
        synthetic = record["synthetic"]
        if not isinstance(is_demo, bool) or not isinstance(synthetic, bool):
            raise ManifestError(f"line {line_number}: is_demo and synthetic must be booleans")
        if fixture_kind == SYNTHETIC_KIND and not (is_demo and synthetic):
            raise ManifestError(
                f"line {line_number}: synthetic fixtures must be labelled demo/synthetic"
            )
        if fixture_kind == FIELD_KIND and (is_demo or synthetic):
            raise ManifestError(
                f"line {line_number}: field datasets must not be labelled demo/synthetic"
            )

        features = validate_feature_vector(
            record["features"],
            expected_dim=feature_dim,
            context=f"line {line_number} features",
        )

        previous = group_labels.setdefault(group_id, label)
        if previous != label:
            raise ManifestError(f"group '{group_id}' spans multiple labels: {previous} and {label}")

        items.append(
            DatasetItem(
                image_id=image_id,
                group_id=group_id,
                label=label,
                features=features,
                is_demo=is_demo,
                synthetic=synthetic,
            )
        )

    if not items:
        raise ManifestError("dataset contains no items")
    return tuple(items)


def _data_fingerprint(items: tuple[DatasetItem, ...]) -> str:
    canonical = [
        {
            "image_id": item.image_id,
            "group_id": item.group_id,
            "label": item.label,
            "features": list(item.features),
        }
        for item in sorted(items, key=lambda entry: entry.image_id)
    ]
    return hashlib.sha256(canonical_json_bytes(canonical)).hexdigest()


def load_manifest(path: str | Path) -> DatasetManifest:
    """Load and fully validate a dataset manifest and its data file."""

    manifest_path = Path(path)
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ManifestError(f"manifest not found: {manifest_path}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestError(f"manifest unreadable: {manifest_path}") from error
    if not isinstance(raw, dict):
        raise ManifestError("manifest must be a JSON object")

    for key in REQUIRED_KEYS:
        if key not in raw:
            raise ManifestError(f"manifest is missing '{key}'")

    fixture_kind = _validate_fixture_kind(raw)
    classes = _load_classes(raw)
    class_labels = {entry.label for entry in classes}
    feature_dim = _require_int(raw, "feature_dim")

    data_file = Path(_require_string(raw, "data_file"))
    if not data_file.is_absolute():
        data_file = manifest_path.parent / data_file
    try:
        data_bytes = data_file.read_bytes()
    except OSError as error:
        raise ManifestError(f"dataset file unreadable: {data_file}") from error

    declared_sha = _require_string(raw, "data_sha256")
    actual_sha = hashlib.sha256(data_bytes).hexdigest()
    if declared_sha != actual_sha:
        raise ManifestError("data_sha256 does not match the dataset file")

    items = _load_items(
        data_file,
        fixture_kind=fixture_kind,
        class_labels=class_labels,
        feature_dim=feature_dim,
    )

    if "items_count" in raw:
        declared_count = raw["items_count"]
        if (
            isinstance(declared_count, bool)
            or not isinstance(declared_count, int)
            or declared_count != len(items)
        ):
            raise ManifestError("items_count does not match the dataset")

    return DatasetManifest(
        path=manifest_path,
        dataset_id=_require_string(raw, "dataset_id"),
        description=_require_string(raw, "description"),
        fixture_kind=fixture_kind,
        is_demo=_require_bool(raw, "is_demo"),
        created_at=_require_string(raw, "created_at"),
        licence=_require_string(raw, "licence"),
        provenance=_require_string(raw, "provenance"),
        feature_contract_version=_require_string(raw, "feature_contract_version"),
        feature_dim=feature_dim,
        taxonomy_version=_require_string(raw, "taxonomy_version"),
        classes=classes,
        items=items,
        data_sha256=actual_sha,
        data_fingerprint=_data_fingerprint(items),
    )

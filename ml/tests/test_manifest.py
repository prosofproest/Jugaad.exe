from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from pest_ml.manifest import ManifestError, load_manifest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _fixture_copy(tmp_path: Path) -> tuple[Path, dict]:
    shutil.copy(FIXTURES / "synthetic_dataset.jsonl", tmp_path / "synthetic_dataset.jsonl")
    raw = json.loads((FIXTURES / "synthetic_manifest.json").read_text(encoding="utf-8"))
    return tmp_path, raw


def _write_manifest(directory: Path, raw: dict) -> Path:
    path = directory / "synthetic_manifest.json"
    path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_records(directory: Path, raw: dict, records: list[dict]) -> None:
    text = "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n"
    data = text.encode("utf-8")
    (directory / "synthetic_dataset.jsonl").write_bytes(data)
    raw["data_sha256"] = hashlib.sha256(data).hexdigest()
    raw["items_count"] = len(records)


def test_loads_valid_manifest(manifest_path) -> None:
    manifest = load_manifest(manifest_path)
    assert manifest.dataset_id == "synthetic-image-triage-fixture-v1"
    assert len(manifest.items) == 90
    assert manifest.feature_dim == 4


def test_rejects_field_dataset_without_permissions(tmp_path: Path) -> None:
    directory, raw = _fixture_copy(tmp_path)
    raw["fixture_kind"] = "field_dataset"
    raw["is_demo"] = False
    raw.pop("permissions", None)
    with pytest.raises(ManifestError, match="permissions"):
        load_manifest(_write_manifest(directory, raw))


def test_field_dataset_requires_privacy_review_for_personal_data(tmp_path: Path) -> None:
    directory, raw = _fixture_copy(tmp_path)
    raw["fixture_kind"] = "field_dataset"
    raw["is_demo"] = False
    raw["licence"] = "CC-BY-4.0"
    raw["personal_data"] = True
    raw["permissions"] = {
        "consent_ref": "consent-1",
        "ethics_ref": "ethics-1",
        "data_owner": "owner",
    }
    with pytest.raises(ManifestError, match="privacy_review_ref"):
        load_manifest(_write_manifest(directory, raw))


def test_rejects_checksum_mismatch(tmp_path: Path) -> None:
    directory, raw = _fixture_copy(tmp_path)
    raw["data_sha256"] = "0" * 64
    with pytest.raises(ManifestError, match="data_sha256"):
        load_manifest(_write_manifest(directory, raw))


def test_rejects_group_that_spans_labels(tmp_path: Path) -> None:
    directory, raw = _fixture_copy(tmp_path)
    _write_records(
        directory,
        raw,
        [
            {
                "image_id": "a",
                "group_id": "shared-group",
                "label": "lesion_like",
                "features": [0.1, 0.2, 0.3, 0.4],
                "is_demo": True,
                "synthetic": True,
            },
            {
                "image_id": "b",
                "group_id": "shared-group",
                "label": "healthy_like",
                "features": [0.4, 0.3, 0.2, 0.1],
                "is_demo": True,
                "synthetic": True,
            },
        ],
    )
    with pytest.raises(ManifestError, match="spans multiple labels"):
        load_manifest(_write_manifest(directory, raw))


def test_rejects_unknown_label(tmp_path: Path) -> None:
    directory, raw = _fixture_copy(tmp_path)
    _write_records(
        directory,
        raw,
        [
            {
                "image_id": "a",
                "group_id": "g",
                "label": "not_in_taxonomy",
                "features": [0.1, 0.2, 0.3, 0.4],
                "is_demo": True,
                "synthetic": True,
            }
        ],
    )
    with pytest.raises(ManifestError, match="unknown label"):
        load_manifest(_write_manifest(directory, raw))


def test_synthetic_items_must_be_labelled(tmp_path: Path) -> None:
    directory, raw = _fixture_copy(tmp_path)
    _write_records(
        directory,
        raw,
        [
            {
                "image_id": "a",
                "group_id": "g",
                "label": "lesion_like",
                "features": [0.1, 0.2, 0.3, 0.4],
                "is_demo": False,
                "synthetic": True,
            }
        ],
    )
    with pytest.raises(ManifestError, match="demo/synthetic"):
        load_manifest(_write_manifest(directory, raw))

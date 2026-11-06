from __future__ import annotations

import json
from pathlib import Path

from pest_ml.manifest import load_manifest
from pest_ml.synthetic import build_dataset

ML_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ML_ROOT / "fixtures"
CONTRACT = ML_ROOT / "contract"


def test_committed_fixture_matches_generator() -> None:
    data_text, manifest_text = build_dataset()
    assert (FIXTURES / "synthetic_dataset.jsonl").read_bytes() == data_text.encode("utf-8")
    assert (FIXTURES / "synthetic_manifest.json").read_bytes() == manifest_text.encode("utf-8")


def test_synthetic_manifest_is_labelled(manifest_path) -> None:
    manifest = load_manifest(manifest_path)
    assert manifest.fixture_kind == "synthetic_fixture"
    assert manifest.is_demo is True
    assert all(item.is_demo and item.synthetic for item in manifest.items)
    assert manifest.class_labels == ("lesion_like", "healthy_like", "other_like")


def test_label_map_matches_manifest(manifest_path) -> None:
    manifest = load_manifest(manifest_path)
    label_map = json.loads((CONTRACT / "label_map.synthetic.json").read_text(encoding="utf-8"))
    assert label_map["is_demo"] is True
    assert tuple(entry["label"] for entry in label_map["classes"]) == manifest.class_labels


def test_schema_is_valid_json() -> None:
    schema = json.loads((CONTRACT / "dataset-manifest.schema.json").read_text(encoding="utf-8"))
    assert schema["title"] == "PS-03 dataset manifest"
    assert "fixture_kind" in schema["properties"]

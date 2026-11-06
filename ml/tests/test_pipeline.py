from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from app.modules.assessments.registry import ModelRegistry
from pest_ml.pipeline import run_pipeline
from pest_ml.promote import PromotionError, build_registry_entry
from pest_ml.train import load_artefact

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
ARTEFACT_FILES = (
    "model.json",
    "split_report.json",
    "evaluation_report.json",
    "registry_entry.json",
    "model_card.md",
    "pipeline_summary.json",
)


def _run(tmp_path: Path, name: str = "run") -> Path:
    run_pipeline(FIXTURES / "synthetic_manifest.json", tmp_path / name)
    return tmp_path / name


def test_pipeline_writes_verifiable_artefacts(tmp_path: Path) -> None:
    out = _run(tmp_path)
    for filename in ARTEFACT_FILES:
        assert (out / filename).is_file()

    report = json.loads((out / "evaluation_report.json").read_text(encoding="utf-8"))
    assert report["is_demo"] is True
    assert report["metric_provenance"] == "synthetic_fixture"
    assert report["n_total"] == 18
    assert report["calibration"] is None
    assert 0.0 <= report["macro_f1"] <= 1.0

    entry = json.loads((out / "registry_entry.json").read_text(encoding="utf-8"))
    registry = ModelRegistry.model_validate({"schema_version": "1.0", "models": [entry]})
    assert registry.models[0].status == "evaluated"
    assert registry.models[0].is_demo is True

    model = load_artefact(out / "model.json")
    assert model.checksum == entry["sha256"]
    file_sha = hashlib.sha256((out / "model.json").read_bytes()).hexdigest()
    assert file_sha == entry["sha256"]

    card = (out / "model_card.md").read_text(encoding="utf-8")
    assert "SYNTHETIC FIXTURE" in card
    assert "not a performance claim" in card


def test_pipeline_is_byte_reproducible(tmp_path: Path) -> None:
    first = _run(tmp_path, "first")
    second = _run(tmp_path, "second")
    for filename in ARTEFACT_FILES:
        assert (first / filename).read_bytes() == (second / filename).read_bytes()


def test_synthetic_fixture_cannot_be_approved(tmp_path: Path) -> None:
    out = _run(tmp_path)
    model = load_artefact(out / "model.json")
    report = json.loads((out / "evaluation_report.json").read_text(encoding="utf-8"))
    with pytest.raises(PromotionError, match="synthetic_fixture_cannot_be_approved"):
        build_registry_entry(
            model,
            report,
            artefact_path="artifacts/model.json",
            requested_status="approved",
            approved_at="2026-11-07T00:00:00Z",
            calibration_version="calibration-1",
            calibration_approved=True,
        )

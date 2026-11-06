from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from pest_ml.pipeline import run_pipeline
from pest_ml.promote import PromotionError, build_registry_entry
from pest_ml.train import load_artefact

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _run_artefacts(tmp_path: Path):
    out = tmp_path / "run"
    run_pipeline(FIXTURES / "synthetic_manifest.json", out)
    model = load_artefact(out / "model.json")
    report = json.loads((out / "evaluation_report.json").read_text(encoding="utf-8"))
    return model, report


def test_rejects_checksum_mismatch(tmp_path: Path) -> None:
    model, report = _run_artefacts(tmp_path)
    tampered = dict(report)
    tampered["model_checksum"] = "0" * 64
    with pytest.raises(PromotionError, match="checksum"):
        build_registry_entry(model, tampered, artefact_path="artifacts/model.json")


def test_synthetic_metrics_require_demo_label(tmp_path: Path) -> None:
    model, report = _run_artefacts(tmp_path)
    unlabelled = replace(model, is_demo=False)
    with pytest.raises(PromotionError, match="is_demo"):
        build_registry_entry(unlabelled, report, artefact_path="artifacts/model.json")


def test_approval_requires_calibration(tmp_path: Path) -> None:
    model, report = _run_artefacts(tmp_path)
    validated = replace(model, is_demo=False, metric_provenance="validation")
    updated = dict(report)
    updated["model_checksum"] = validated.checksum
    with pytest.raises(PromotionError, match="calibration"):
        build_registry_entry(
            validated,
            updated,
            artefact_path="artifacts/model.json",
            requested_status="approved",
            approved_at="2026-11-07T00:00:00Z",
        )


def test_non_demo_entry_can_reach_evaluated(tmp_path: Path) -> None:
    model, report = _run_artefacts(tmp_path)
    validated = replace(model, is_demo=False, metric_provenance="validation")
    updated = dict(report)
    updated["model_checksum"] = validated.checksum
    entry = build_registry_entry(
        validated,
        updated,
        artefact_path="artifacts/model.json",
        requested_status="evaluated",
    )
    assert entry.status == "evaluated"
    assert entry.is_demo is False
    assert entry.metric_provenance == "validation"
    assert entry.approved_at is None

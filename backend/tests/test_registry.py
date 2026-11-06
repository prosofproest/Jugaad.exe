from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.modules.assessments.registry import (
    ModelNotApproved,
    ModelRegistry,
    RegistryEntry,
    load_registry_file,
)

from tests.support import write_registry_file


def make_entry(tmp_path: Path, **overrides) -> dict:
    artefact = tmp_path / "artefact.bin"
    artefact.write_bytes(b"synthetic test artefact, not a model\n")
    entry = {
        "model_version": "synthetic-model-1",
        "status": "approved",
        "artefact_path": str(artefact.resolve()),
        "sha256": hashlib.sha256(artefact.read_bytes()).hexdigest(),
        "taxonomy_version": "synthetic-taxonomy-1",
        "preprocessing_version": "prep-synthetic-1",
        "calibration_version": None,
        "calibration_approved": False,
        "metrics": None,
        "metric_provenance": None,
        "is_demo": True,
        "created_at": "2026-11-06T00:00:00Z",
        "approved_at": "2026-11-06T00:00:00Z",
    }
    entry.update(overrides)
    return entry


def test_approved_entry_with_matching_checksum_is_servable(tmp_path: Path) -> None:
    registry = ModelRegistry.model_validate(
        {"schema_version": "1.0", "models": [make_entry(tmp_path)]}
    )

    served = registry.require_servable(
        "synthetic-model-1", taxonomy_version="synthetic-taxonomy-1"
    )

    assert served.model_version == "synthetic-model-1"
    assert served.preprocessing_version == "prep-synthetic-1"


@pytest.mark.parametrize(
    ("overrides", "expected_code"),
    [
        ({"status": "evaluated", "approved_at": None}, "model_not_approved"),
        ({"status": "trained", "approved_at": None}, "model_not_approved"),
        ({"status": "rejected", "approved_at": None}, "model_not_approved"),
        ({"status": "retired", "approved_at": None}, "model_retired"),
        ({"sha256": "0" * 64}, "artefact_checksum_mismatch"),
        ({"artefact_path": "does-not-exist.bin"}, "artefact_missing"),
    ],
)
def test_unservable_entries_are_refused(tmp_path: Path, overrides, expected_code) -> None:
    registry = ModelRegistry.model_validate(
        {"schema_version": "1.0", "models": [make_entry(tmp_path, **overrides)]}
    )

    with pytest.raises(ModelNotApproved) as caught:
        registry.require_servable(
            "synthetic-model-1", taxonomy_version="synthetic-taxonomy-1"
        )

    assert caught.value.code == expected_code


def test_unknown_model_version_is_refused(tmp_path: Path) -> None:
    registry = ModelRegistry.model_validate(
        {"schema_version": "1.0", "models": [make_entry(tmp_path)]}
    )

    with pytest.raises(ModelNotApproved) as caught:
        registry.require_servable("unknown", taxonomy_version="synthetic-taxonomy-1")

    assert caught.value.code == "unknown_model_version"


def test_taxonomy_mismatch_is_refused(tmp_path: Path) -> None:
    registry = ModelRegistry.model_validate(
        {"schema_version": "1.0", "models": [make_entry(tmp_path)]}
    )

    with pytest.raises(ModelNotApproved) as caught:
        registry.require_servable("synthetic-model-1", taxonomy_version="other-taxonomy")

    assert caught.value.code == "taxonomy_version_mismatch"


def test_approved_calibration_requires_a_matching_version(tmp_path: Path) -> None:
    registry = ModelRegistry.model_validate(
        {
            "schema_version": "1.0",
            "models": [
                make_entry(
                    tmp_path,
                    calibration_approved=True,
                    calibration_version="cal-synthetic-1",
                )
            ],
        }
    )

    with pytest.raises(ModelNotApproved) as caught:
        registry.require_servable(
            "synthetic-model-1", taxonomy_version="synthetic-taxonomy-1"
        )
    assert caught.value.code == "calibration_version_required"

    with pytest.raises(ModelNotApproved) as caught:
        registry.require_servable(
            "synthetic-model-1",
            taxonomy_version="synthetic-taxonomy-1",
            calibration_version="cal-other",
        )
    assert caught.value.code == "calibration_version_mismatch"

    served = registry.require_servable(
        "synthetic-model-1",
        taxonomy_version="synthetic-taxonomy-1",
        calibration_version="cal-synthetic-1",
    )
    assert served.calibration_version == "cal-synthetic-1"


def test_synthetic_metrics_must_be_labelled_as_demo(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        RegistryEntry.model_validate(
            make_entry(
                tmp_path,
                metrics={"macro_f1": 0.9},
                metric_provenance="synthetic_fixture",
                is_demo=False,
            )
        )


def test_metrics_require_provenance(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        RegistryEntry.model_validate(make_entry(tmp_path, metrics={"macro_f1": 0.9}))


def test_registry_file_round_trip(tmp_path: Path) -> None:
    registry = ModelRegistry.model_validate(
        {"schema_version": "1.0", "models": [make_entry(tmp_path)]}
    )
    path = write_registry_file(tmp_path / "registry.json", registry)

    loaded = load_registry_file(path)

    assert loaded.find("synthetic-model-1") is not None

from __future__ import annotations

import math
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.modules.assessments.calibration import TemperatureCalibration
from app.modules.assessments.inference import InferenceFailure

from tests.support import (
    FIXED_TIME,
    FakeAdapter,
    make_registry,
    make_request,
    make_service,
)

LOW_MARGIN_LOGITS = [math.log(0.565), math.log(0.42), math.log(0.015)]


def test_assessed_prediction_is_persisted_with_lineage_and_thresholds(tmp_path: Path) -> None:
    service, store = make_service(tmp_path)
    request = make_request()

    response = service.assess(request)

    assert response.state == "assessed"
    assert response.reason_code is None
    assert response.calibrated is False
    assert response.confidence_band == "not_calibrated"
    assert response.candidates
    assert all(candidate.score is None for candidate in response.candidates)
    assert response.assessment_id is not None
    assert response.generated_at == FIXED_TIME

    record = store.get(response.assessment_id)
    assert record is not None
    assert record.input_snapshot_ref == f"sha256:{request.image.content_hash}"
    assert record.quality_gate_version == "qg-synthetic-1"
    assert record.decision_thresholds["tau_c"]["lesion_like"] == 0.55
    assert record.decision_thresholds["margin"] == 0.15
    assert record.decision_thresholds["entropy"] == 0.7
    assert record.decision_thresholds["ood_max"] == 0.4
    assert record.scores is not None
    assert record.preprocessing_version == "prep-synthetic-1"
    assert record.not_a_diagnosis is True
    assert store.count() == 1


def test_calibrated_prediction_exposes_band_and_scores(tmp_path: Path) -> None:
    # Serving wiring is tested with an identity-temperature artefact; the
    # fitting algorithm itself is covered in test_calibration.py.
    calibration = TemperatureCalibration(
        version="cal-synthetic-1",
        temperature=1.0,
        n_samples=20,
        fitted_on="calibration_split",
        data_fingerprint="synthetic-fixture",
        checksum="b" * 64,
    )
    service, store = make_service(tmp_path, calibration=calibration)

    response = service.assess(make_request())

    assert response.state == "assessed"
    assert response.calibrated is True
    assert response.calibration_version == "cal-synthetic-1"
    assert response.confidence_band in {"low", "medium", "high"}
    assert all(candidate.score is not None for candidate in response.candidates)
    assert response.decision_thresholds is not None
    assert response.decision_thresholds["score_kind"] == "calibrated_probability"

    record = store.get(response.assessment_id or "")
    assert record is not None
    assert record.calibration_version == "cal-synthetic-1"
    assert record.calibrated is True


def test_approved_calibration_without_the_artefact_fails_safe(tmp_path: Path) -> None:
    registry, _ = make_registry(
        tmp_path,
        calibration_approved=True,
        calibration_version="cal-synthetic-1",
    )
    service, store = make_service(tmp_path, registry=registry, calibration=None)

    response = service.assess(make_request())

    assert response.state == "failed"
    assert response.error_code in {"calibration_version_required", "calibration_unavailable"}
    assert response.retryable is False
    assert store.count() == 0


def test_unapproved_model_fails_safe(tmp_path: Path) -> None:
    registry, _ = make_registry(tmp_path, status="evaluated")
    adapter = FakeAdapter()
    service, store = make_service(tmp_path, registry=registry, adapter=adapter)

    response = service.assess(make_request())

    assert response.state == "failed"
    assert response.error_code == "model_not_approved"
    assert response.retryable is False
    assert adapter.calls == []
    assert store.count() == 0


def test_quality_failure_abstains_before_inference(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    service, store = make_service(tmp_path, adapter=adapter)

    response = service.assess(make_request(laplacian_variance=1.0))

    assert response.state == "abstained"
    assert response.reason_code == "quality_gate_failed"
    assert response.quality_flag == "blurry"
    assert "blurry" in response.quality_flags
    assert response.candidates == []
    assert "not a diagnosis" in response.reason_text.lower()
    assert adapter.calls == []
    assert store.count() == 1


def test_unsupported_crop_abstains_without_inference(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    service, store = make_service(tmp_path, adapter=adapter)

    response = service.assess(make_request(crop_id="not_supported"))

    assert response.state == "unsupported_crop"
    assert response.reason_code == "unsupported_crop"
    assert response.supported_crops == ["test_crop"]
    assert response.candidates == []
    assert adapter.calls == []
    record = store.get(response.assessment_id or "")
    assert record is not None
    assert record.quality_result == "not_run"


def test_same_client_id_is_idempotent(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    service, store = make_service(tmp_path, adapter=adapter)
    request = make_request(client_assessment_id="same-id")

    first = service.assess(request)
    second = service.assess(request)

    assert first.assessment_id == second.assessment_id
    assert adapter.calls and len(adapter.calls) == 1
    assert store.count() == 1


def test_inference_timeout_returns_a_safe_retryable_failure(tmp_path: Path) -> None:
    adapter = FakeAdapter(delay_s=0.3)
    service, store = make_service(tmp_path, adapter=adapter, timeout_s=0.05)

    response = service.assess(make_request())

    assert response.state == "failed"
    assert response.error_code == "inference_timeout"
    assert response.retryable is True
    assert response.assessment_id is None
    assert store.count() == 0


def test_inference_exception_returns_a_safe_failure(tmp_path: Path) -> None:
    adapter = FakeAdapter(error=RuntimeError("boom"))
    service, store = make_service(tmp_path, adapter=adapter)

    response = service.assess(make_request())

    assert response.state == "failed"
    assert response.error_code == "inference_error"
    assert response.retryable is True
    assert store.count() == 0


def test_inference_failure_code_is_preserved(tmp_path: Path) -> None:
    adapter = FakeAdapter(error=InferenceFailure("inference_not_configured", retryable=False))
    service, _ = make_service(tmp_path, adapter=adapter)

    response = service.assess(make_request())

    assert response.state == "failed"
    assert response.error_code == "inference_not_configured"
    assert response.retryable is False


def test_label_map_mismatch_fails_safe(tmp_path: Path) -> None:
    adapter = FakeAdapter(logits={"lesion_like": 1.0, "healthy_like": 0.0})
    service, store = make_service(tmp_path, adapter=adapter)

    response = service.assess(make_request())

    assert response.state == "failed"
    assert response.error_code == "label_map_mismatch"
    assert store.count() == 0


def test_low_margin_abstention_has_no_candidates(tmp_path: Path) -> None:
    adapter = FakeAdapter(logits=dict(zip(["lesion_like", "healthy_like", "other_like"], LOW_MARGIN_LOGITS, strict=True)))
    service, store = make_service(tmp_path, adapter=adapter)

    response = service.assess(make_request())

    assert response.state == "abstained"
    assert response.reason_code == "low_margin"
    assert response.candidates == []
    assert response.confidence_band is None
    record = store.get(response.assessment_id or "")
    assert record is not None
    assert record.abstained is True
    assert record.abstain_reason == "low_margin"


def test_prediction_records_are_append_only(tmp_path: Path) -> None:
    service, store = make_service(tmp_path)
    response = service.assess(make_request())
    record = store.get(response.assessment_id or "")
    assert record is not None

    with pytest.raises(ValidationError):
        record.state = "tampered"  # type: ignore[misc]

    assert not hasattr(store, "update")
    assert not hasattr(store, "delete")


def test_history_is_paginated_newest_first(tmp_path: Path) -> None:
    service, _ = make_service(tmp_path)
    for index in range(3):
        service.assess(make_request(client_assessment_id=f"client-{index}"))

    first_page = service.history(limit=2)
    second_page = service.history(limit=2, cursor=first_page.next_cursor)

    assert len(first_page.items) == 2
    assert first_page.next_cursor == "2"
    assert len(second_page.items) == 1
    assert second_page.next_cursor is None
    assert first_page.items[0].assessment_id != second_page.items[0].assessment_id

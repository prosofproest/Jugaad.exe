from __future__ import annotations

import pytest
from app.modules.assessments.calibration import (
    CalibrationError,
    CalibrationNotApproved,
    calibration_diagnostics,
    fit_temperature,
    softmax,
)

LABELS = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
# Deliberately overconfident and half-wrong: temperature scaling should soften it.
LOGITS = [[3.0, 0.0, 0.0] if index % 2 == 0 else [0.0, 3.0, 0.0] for index in range(20)]
# Label 1 on half of them, so the confident peak is wrong half the time.
MIXED_LABELS = [0, 0, 1, 1] * 5


def test_softmax_is_stable_and_normalised() -> None:
    probabilities = softmax([1000.0, 1000.0, -1000.0])

    assert sum(probabilities) == pytest.approx(1.0)
    assert probabilities[0] == pytest.approx(probabilities[1])
    assert probabilities[2] == pytest.approx(0.0)


def test_fit_refuses_a_split_below_the_configured_minimum() -> None:
    with pytest.raises(CalibrationNotApproved) as caught:
        fit_temperature(
            LOGITS,
            LABELS,
            version="cal-synthetic-1",
            data_fingerprint="synthetic-fixture",
            min_samples=21,
        )

    assert caught.value.code == "insufficient_calibration_samples"


def test_fit_reduces_negative_log_likelihood_on_an_overconfident_set() -> None:
    calibration = fit_temperature(
        LOGITS,
        MIXED_LABELS,
        version="cal-synthetic-1",
        data_fingerprint="synthetic-fixture",
        min_samples=10,
    )

    before = calibration_diagnostics([softmax(row) for row in LOGITS], MIXED_LABELS)
    after = calibration_diagnostics([calibration.apply(row) for row in LOGITS], MIXED_LABELS)

    assert calibration.temperature > 1.0
    assert after.nll < before.nll
    assert after.brier < before.brier


def test_calibration_artefact_is_deterministic_and_identifiable() -> None:
    first = fit_temperature(
        LOGITS,
        MIXED_LABELS,
        version="cal-synthetic-1",
        data_fingerprint="synthetic-fixture",
        min_samples=10,
    )
    second = fit_temperature(
        LOGITS,
        MIXED_LABELS,
        version="cal-synthetic-1",
        data_fingerprint="synthetic-fixture",
        min_samples=10,
    )
    changed = fit_temperature(
        LOGITS,
        MIXED_LABELS,
        version="cal-synthetic-2",
        data_fingerprint="synthetic-fixture",
        min_samples=10,
    )

    assert first.temperature == second.temperature
    assert first.checksum == second.checksum
    assert first.checksum != changed.checksum
    assert first.n_samples == len(LOGITS)
    assert first.fitted_on == "calibration_split"


def test_diagnostics_of_a_perfect_forecast_are_zero() -> None:
    diagnostics = calibration_diagnostics([[1.0, 0.0], [0.0, 1.0]], [0, 1])

    assert diagnostics.nll == pytest.approx(0.0)
    assert diagnostics.brier == pytest.approx(0.0)
    assert diagnostics.ece == pytest.approx(0.0)
    assert diagnostics.n_samples == 2


def test_diagnostics_reject_unnormalised_probabilities() -> None:
    with pytest.raises(CalibrationError):
        calibration_diagnostics([[0.7, 0.7]], [0])


def test_fit_rejects_a_label_outside_the_class_set() -> None:
    with pytest.raises(CalibrationError):
        fit_temperature(
            [[1.0, 0.0], [0.0, 1.0]],
            [0, 5],
            version="cal-synthetic-1",
            data_fingerprint="synthetic-fixture",
            min_samples=1,
        )

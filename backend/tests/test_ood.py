from __future__ import annotations

import pytest
from app.modules.assessments.calibration import CalibrationError
from app.modules.assessments.ood import (
    evaluate_ood,
    fit_ood_threshold,
    ood_score_from_logits,
)


def test_ood_score_is_bounded_and_higher_for_a_flat_prediction() -> None:
    confident = ood_score_from_logits([5.0, 0.0, 0.0])
    flat = ood_score_from_logits([0.0, 0.0, 0.0])

    assert 0.0 <= confident <= 1.0
    assert 0.0 <= flat <= 1.0
    assert flat > confident


def test_threshold_fitting_respects_the_declared_false_accept_rate() -> None:
    known = [0.05] * 9 + [0.5]

    threshold = fit_ood_threshold(known, max_false_accept_rate=0.1)

    assert threshold == pytest.approx(0.05)
    report = evaluate_ood(known, [0.9], threshold=threshold)
    assert report.false_accept_rate == pytest.approx(0.1)


def test_a_strict_rate_with_a_small_panel_allows_zero_false_accepts() -> None:
    threshold = fit_ood_threshold([0.1, 0.2, 0.3], max_false_accept_rate=0.0)

    assert threshold == pytest.approx(0.3)
    report = evaluate_ood([0.1, 0.2, 0.3], [0.4], threshold=threshold)
    assert report.false_accept_rate == 0.0


def test_separated_scores_give_perfect_auroc_and_detection() -> None:
    report = evaluate_ood([0.1, 0.2], [0.7, 0.9], threshold=0.4)

    assert report.auroc == 1.0
    assert report.false_accept_rate == 0.0
    assert report.detection_rate == 1.0
    assert report.n_known == 2
    assert report.n_unknown == 2


def test_tied_scores_count_as_half() -> None:
    report = evaluate_ood([0.5], [0.5], threshold=0.9)

    assert report.auroc == 0.5


def test_ood_inputs_are_validated() -> None:
    with pytest.raises(CalibrationError):
        fit_ood_threshold([], max_false_accept_rate=0.1)
    with pytest.raises(CalibrationError):
        fit_ood_threshold([0.1], max_false_accept_rate=1.5)
    with pytest.raises(CalibrationError):
        evaluate_ood([], [0.9], threshold=0.5)
    with pytest.raises(CalibrationError):
        evaluate_ood([0.1], [1.5], threshold=0.5)

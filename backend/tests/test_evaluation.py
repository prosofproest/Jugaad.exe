from __future__ import annotations

import pytest
from app.modules.assessments.calibration import CalibrationError
from app.modules.assessments.evaluation import EvaluationSample, evaluate_classifier

LABELS = ["class_a", "class_b", "class_c"]


def sample(true_label: str, predicted: str, *, assessed: bool = True) -> EvaluationSample:
    probabilities = {label: 0.0 for label in LABELS}
    probabilities[predicted] = 1.0
    return EvaluationSample(
        true_label=true_label,
        probabilities=probabilities,
        assessed=assessed,
    )


def test_perfect_assessed_set_reports_per_class_and_top_k_metrics() -> None:
    samples = [
        sample("class_a", "class_a"),
        sample("class_a", "class_a"),
        sample("class_b", "class_b"),
        sample("class_c", "class_c"),
    ]

    report = evaluate_classifier(samples, LABELS, calibration_approved=False)

    assert report.n_total == 4
    assert report.n_assessed == 4
    assert report.abstention_rate == 0.0
    assert report.macro_f1 == pytest.approx(1.0)
    assert report.per_class["class_a"].support == 2
    assert report.per_class["class_a"].precision == 1.0
    assert report.confusion["class_a"]["class_a"] == 2
    assert report.top_k_accuracy[1] == 1.0
    assert report.top_k_accuracy[3] == 1.0
    assert report.calibration is None


def test_abstained_images_are_excluded_and_reported_beside_the_metrics() -> None:
    samples = [
        sample("class_a", "class_a"),
        sample("class_b", "class_b"),
        sample("class_a", "class_a", assessed=False),
        sample("class_b", "class_b", assessed=False),
    ]

    report = evaluate_classifier(samples, LABELS, calibration_approved=False)

    assert report.n_assessed == 2
    assert report.n_abstained == 2
    assert report.abstention_rate == pytest.approx(0.5)
    assert report.macro_f1 == pytest.approx(1.0)
    assert report.per_class["class_a"].support == 1


def test_errors_are_counted_per_class() -> None:
    samples = [
        sample("class_a", "class_b"),
        sample("class_b", "class_b"),
    ]

    report = evaluate_classifier(samples, LABELS, calibration_approved=False)

    assert report.confusion["class_a"]["class_b"] == 1
    assert report.per_class["class_a"].recall == 0.0
    assert report.per_class["class_b"].precision == 0.5
    assert report.per_class["class_b"].recall == 1.0
    assert report.per_class["class_b"].f1 == pytest.approx(2 * 0.5 * 1.0 / 1.5)
    assert report.macro_f1 == pytest.approx((0.0 + (2 * 0.5 * 1.0 / 1.5)) / 2)
    assert report.top_k_accuracy[1] == pytest.approx(0.5)


def test_calibration_is_only_reported_when_approved() -> None:
    samples = [sample("class_a", "class_a"), sample("class_b", "class_b")]

    approved = evaluate_classifier(samples, LABELS, calibration_approved=True)

    assert approved.calibration is not None
    assert approved.calibration.n_samples == 2
    assert approved.calibration.ece == pytest.approx(0.0)


def test_an_empty_set_or_bad_probabilities_are_rejected() -> None:
    with pytest.raises(CalibrationError):
        evaluate_classifier([], LABELS, calibration_approved=False)

    with pytest.raises(CalibrationError):
        evaluate_classifier(
            [
                EvaluationSample(
                    true_label="class_a",
                    probabilities={"class_a": 0.7, "class_b": 0.7, "class_c": 0.0},
                    assessed=True,
                )
            ],
            LABELS,
            calibration_approved=False,
        )

    with pytest.raises(CalibrationError):
        evaluate_classifier(
            [
                EvaluationSample(
                    true_label="not_in_taxonomy",
                    probabilities={"class_a": 1.0, "class_b": 0.0, "class_c": 0.0},
                    assessed=True,
                )
            ],
            LABELS,
            calibration_approved=False,
        )

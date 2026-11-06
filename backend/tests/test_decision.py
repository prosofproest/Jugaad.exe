from __future__ import annotations

import pytest
from app.modules.assessments.decision import DecisionError, decide, normalised_entropy

from tests.support import make_policy

POLICY = make_policy()


def scores(lesion: float, healthy: float, other: float) -> dict[str, float]:
    return {
        "lesion_like": lesion,
        "healthy_like": healthy,
        "other_like": other,
    }


def test_all_gates_passing_returns_assessed_with_at_most_three_candidates() -> None:
    decision = decide(scores(0.85, 0.10, 0.05), ood_score=0.1, calibrated=True, policy=POLICY)

    assert decision.state == "assessed"
    assert decision.reason_code is None
    assert len(decision.candidates) == 3
    assert decision.candidates[0].label == "lesion_like"
    assert decision.confidence_band == "high"
    assert decision.abstained is False


def test_top_candidate_below_its_class_threshold_abstains() -> None:
    decision = decide(scores(0.50, 0.30, 0.20), ood_score=0.1, calibrated=True, policy=POLICY)

    assert decision.state == "abstained"
    assert decision.reason_code == "below_class_threshold"
    assert decision.candidates == ()


def test_small_margin_abstains() -> None:
    decision = decide(scores(0.565, 0.42, 0.015), ood_score=0.1, calibrated=True, policy=POLICY)

    assert decision.reason_code == "low_margin"
    assert decision.candidates == ()


def test_high_entropy_abstains_even_when_the_top_class_clears_its_threshold() -> None:
    decision = decide(scores(0.56, 0.22, 0.22), ood_score=0.1, calibrated=True, policy=POLICY)

    assert decision.top1_score is not None and decision.top1_score >= 0.55
    assert decision.reason_code == "high_entropy"


def test_out_of_distribution_takes_precedence_over_other_gates() -> None:
    decision = decide(scores(0.85, 0.10, 0.05), ood_score=0.41, calibrated=True, policy=POLICY)

    assert decision.reason_code == "out_of_distribution"


def test_uncalibrated_output_is_qualitative_only() -> None:
    decision = decide(scores(0.85, 0.10, 0.05), ood_score=0.1, calibrated=False, policy=POLICY)

    assert decision.state == "assessed"
    assert decision.calibrated is False
    assert decision.confidence_band == "not_calibrated"


def test_normalised_entropy_is_bounded() -> None:
    assert normalised_entropy(scores(1.0, 0.0, 0.0)) == pytest.approx(0.0)
    assert normalised_entropy(scores(1 / 3, 1 / 3, 1 / 3)) == pytest.approx(1.0)


def test_score_labels_must_match_the_taxonomy() -> None:
    with pytest.raises(DecisionError):
        decide({"lesion_like": 1.0}, ood_score=0.1, calibrated=True, policy=POLICY)


def test_scores_must_form_a_distribution() -> None:
    with pytest.raises(DecisionError):
        decide(scores(0.5, 0.5, 0.5), ood_score=0.1, calibrated=True, policy=POLICY)


def test_ood_score_is_required_when_the_gate_is_enabled() -> None:
    with pytest.raises(DecisionError):
        decide(scores(0.85, 0.10, 0.05), ood_score=None, calibrated=True, policy=POLICY)

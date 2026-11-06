from __future__ import annotations

import pytest
from app.modules.assessments.decision import Decision, decide
from app.modules.assessments.explanation import NOT_A_DIAGNOSIS, explain, validate_safe_text
from app.modules.assessments.quality import ImageMetrics, evaluate_quality

from tests.support import make_policy

POLICY = make_policy()


def abstained(reason: str) -> Decision:
    return Decision(
        state="abstained",
        reason_code=reason,  # type: ignore[arg-type]
        candidates=(),
        confidence_band=None,
        top1_label=None,
        top1_score=None,
        margin=0.0,
        entropy=0.0,
        ood_score=0.0,
        calibrated=False,
    )


def test_assessed_explanation_states_that_it_is_not_a_diagnosis() -> None:
    decision = decide(
        {"lesion_like": 0.85, "healthy_like": 0.10, "other_like": 0.05},
        ood_score=0.1,
        calibrated=True,
        policy=POLICY,
    )

    explanation = explain(decision, POLICY)

    assert explanation.title == "Photo assessment"
    assert NOT_A_DIAGNOSIS in explanation.text
    assert "synthetic lesion-like pattern" in explanation.text
    assert "retake" not in explanation.next_steps
    assert "request_review" in explanation.next_steps
    assert explanation.blocked is False


@pytest.mark.parametrize(
    "reason",
    [
        "below_class_threshold",
        "low_margin",
        "high_entropy",
        "out_of_distribution",
        "unsupported_crop",
    ],
)
def test_every_abstention_carries_a_reason_and_a_next_step(reason: str) -> None:
    explanation = explain(abstained(reason), POLICY, supported_crops=POLICY.supported_crops)

    assert NOT_A_DIAGNOSIS in explanation.text
    assert len(explanation.text) > len(NOT_A_DIAGNOSIS)
    assert explanation.next_steps


def test_quality_failure_text_names_the_specific_flag() -> None:
    quality = evaluate_quality(
        ImageMetrics(
            width=1200,
            height=900,
            laplacian_variance=1.0,
            mean_luma=128.0,
            clipped_fraction=0.0,
            plant_presence=0.9,
        ),
        POLICY.quality,
    )

    explanation = explain(abstained("quality_gate_failed"), POLICY, quality=quality)

    assert "too blurry" in explanation.text
    assert explanation.next_steps == ("retake",)


def test_unsupported_crop_lists_the_supported_crops() -> None:
    explanation = explain(
        abstained("unsupported_crop"),
        POLICY,
        supported_crops=POLICY.supported_crops,
    )

    assert "test_crop" in explanation.text
    assert "change_crop" in explanation.next_steps


@pytest.mark.parametrize(
    "text",
    [
        "Spray glyphosate at 2 g/L on the field.",
        "Apply mancozeb every 10 days per acre.",
        "This is a confirmed diagnosis of late blight.",
        "There is a 100% chance it is blight.",
    ],
)
def test_safety_validator_rejects_prescriptions_and_diagnostic_claims(text: str) -> None:
    assert validate_safe_text(text) is False


def test_safety_validator_allows_plain_assessment_wording() -> None:
    assert validate_safe_text(
        "The image may be consistent with a lesion-like pattern. This is not a diagnosis."
    )

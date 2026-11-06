from __future__ import annotations

import pytest
from app.modules.advisories.validator import (
    AdvisoryContentRejected,
    find_prohibited_matches,
    require_valid_advisory,
    validate_advisory,
)

from tests.support_notifications import make_body, make_draft


def draft_with(body_field: str, text: str):
    body = make_body(**{body_field: text})
    return make_draft(body=body)


def test_safe_advisory_content_is_accepted() -> None:
    draft = make_draft()

    assert validate_advisory(draft) == ()
    require_valid_advisory(draft)


@pytest.mark.parametrize(
    ("field", "text", "expected_code"),
    [
        ("what_to_do_now", "Apply glyphosate to the affected area.", "product_name"),
        ("what_to_do_now", "Use a fungicide on the affected plants.", "chemical_product"),
        ("what_to_do_now", "Mix 2 g per litre before use.", "dose"),
        ("what_to_do_now", "Use 250 ml/acre on the field.", "dose"),
        ("what_to_do_now", "Tank mix with the other product.", "mixture"),
        ("what_to_do_now", "Spray every 7 days until symptoms stop.", "application_interval"),
        ("what_to_do_now", "Observe the pre-harvest interval.", "pre_harvest_interval"),
        ("what_to_do_now", "This product is approved for use on the crop.", "legal_use_claim"),
        ("what_this_is_about", "This will prevent the disease.", "guarantee"),
        ("what_this_is_about", "This confirms late blight.", "diagnosis_claim"),
        ("what_this_is_about", "This is a confirmed outbreak.", "outbreak_claim"),
        ("what_this_is_about", "There is a 100% chance of disease.", "diagnosis_claim"),
    ],
)
def test_each_prohibited_pattern_class_is_rejected(
    field: str, text: str, expected_code: str
) -> None:
    draft = draft_with(field, text)

    issues = validate_advisory(draft)

    assert expected_code in {issue.code for issue in issues}
    with pytest.raises(AdvisoryContentRejected) as caught:
        require_valid_advisory(draft)
    assert expected_code in caught.value.codes


def test_title_and_source_are_validated_too() -> None:
    assert find_prohibited_matches("title", "Glyphosate update")
    assert find_prohibited_matches("source", "Approved for use by the supplier")


def test_what_not_to_assume_must_state_that_it_is_not_a_diagnosis() -> None:
    draft = draft_with("what_not_to_assume", "Watch the field closely for changes.")

    issues = validate_advisory(draft)

    assert {issue.code for issue in issues} == {"missing_not_a_diagnosis"}


def test_rejection_lists_every_matching_issue() -> None:
    draft = draft_with(
        "what_to_do_now",
        "Spray every 7 days and tank mix 2 g per litre of glyphosate.",
    )

    issues = validate_advisory(draft)

    assert {"product_name", "dose", "mixture", "application_interval"} <= {
        issue.code for issue in issues
    }

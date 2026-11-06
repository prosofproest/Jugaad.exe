"""Unit tests for the chat content-safety validator (spec 08 CHAT-10)."""

from __future__ import annotations

import pytest
from app.modules.conversations.validator import VALIDATOR_VERSION, validate_reply


@pytest.mark.parametrize(
    "text",
    [
        "Spray chlorothalonil at 2 g/L.",
        "Apply 5 ml per litre of water.",
        "Use a tank mix of two products.",
        "Follow the pre-harvest interval.",
        "Mix with mancozeb before application.",
        "Spraying is required every week.",
        "Apply urea to the field.",
        "Use a fungicide.",
        "CHLOROTHALONIL",
    ],
)
def test_unsafe_text_is_blocked(text: str) -> None:
    result = validate_reply(text)

    assert result.allowed is False
    assert result.categories
    assert result.version == VALIDATOR_VERSION


@pytest.mark.parametrize(
    "text",
    [
        "The photo is too blurry to assess. Retake it.",
        "Possible symptom match. This is an assistive result, not a diagnosis.",
        "Request expert review or monitor the plant.",
        "No assessment was produced.",
        "Scout the field and remove affected leaves.",
        "",
        None,
    ],
)
def test_safe_text_is_allowed(text: str | None) -> None:
    assert validate_reply(text).allowed is True


def test_multiple_unsafe_categories_are_reported_without_the_text() -> None:
    result = validate_reply("Spray chlorothalonil at 2 g/L.")

    assert result.allowed is False
    assert result.categories == ("application_instruction", "chemical_product", "dosage")
    assert "chlorothalonil" not in repr(result)


def test_candidate_display_name_is_checked_too() -> None:
    result = validate_reply("Possible symptom match.", "Assistive result.", "Apply fungicide")

    assert result.allowed is False
    assert result.categories == ("chemical_product",)


def test_version_is_stable() -> None:
    assert validate_reply("safe").version == "chat-safety-0.1"

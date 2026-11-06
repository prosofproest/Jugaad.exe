"""Plain-language explanations and the safety validator.

Every assessment body must contain "not a diagnosis". The validator is a
defence-in-depth check on the whole rendered message: a template that ever
starts carrying a chemical prescription or a diagnostic claim is replaced by
a safe generic sentence and the block is recorded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from app.modules.assessments.decision import Decision
from app.modules.assessments.policy import TriagePolicy
from app.modules.assessments.quality import QualityOutcome

NOT_A_DIAGNOSIS = "This is not a diagnosis."

# Chemical prescription vocabulary and dosage patterns are prohibited in the
# assessment surface (R5 / CHAT-10). This list is intentionally conservative.
_FORBIDDEN_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(pesticide|insecticide|fungicide|herbicide|nematicide|rodenticide)\b",
        r"\b(glyphosate|chlorpyrifos|mancozeb|carbendazim|imidacloprid|cypermethrin|"
        r"profenofos|monocrotophos|endosulfan|paraquat)\b",
        r"\b(dose|dosage|mixture|tank[\s-]?mix|pre[\s-]?harvest interval|phi)\b",
        r"\b\d+(\.\d+)?\s?(mg|ml|g|kg|cc)\s?(/|per)\s?(l|litre|liter)\b",
        r"\b(spray|apply)\b.*\b(per|every)\b.*\b(acre|hectare|litre|liter)\b",
        r"\b(confirmed diagnosis|definitely)\b|100\s?%",
    )
)

_SAFE_FALLBACK = (
    "A safe assessment could not be shown for this image. " + NOT_A_DIAGNOSIS
)

_QUALITY_TEXT: dict[str, str] = {
    "blurry": "The image is too blurry to assess. Hold the camera steady and retake it.",
    "dark": "The image is too dark to assess. Move into even light and retake it.",
    "overexposed": "The image is too bright to assess. Avoid direct glare and retake it.",
    "low_resolution": "The image is too small to assess. Move closer and retake it at a higher resolution.",
    "no_plant": "No plant is clearly visible. Frame the affected leaf or stem and retake it.",
}

_REASON_TEXT: dict[str, str] = {
    "below_class_threshold": (
        "The image does not clearly match any condition this model was validated on."
    ),
    "low_margin": (
        "More than one condition looks similarly likely, so no single match is reliable."
    ),
    "high_entropy": (
        "The visual evidence is too mixed to choose a reliable match."
    ),
    "out_of_distribution": (
        "The image is outside the range of field images this model was validated on."
    ),
    "unsupported_crop": (
        "This crop is not supported in this release, so no assessment is made."
    ),
}


@dataclass(frozen=True)
class Explanation:
    title: str
    text: str
    next_steps: tuple[str, ...]
    not_a_diagnosis: bool = True
    blocked: bool = False


def validate_safe_text(text: str) -> bool:
    """Return ``False`` when the text contains a prohibited claim or prescription."""

    return not any(pattern.search(text) for pattern in _FORBIDDEN_PATTERNS)


def _safe(text: str) -> tuple[str, bool]:
    if validate_safe_text(text):
        return text, False
    return _SAFE_FALLBACK, True


def explain(
    decision: Decision,
    policy: TriagePolicy,
    *,
    quality: QualityOutcome | None = None,
    supported_crops: Iterable[str] = (),
) -> Explanation:
    """Build the user-facing explanation for a decision.

    The output is deterministic for a given decision and policy so the stored
    message can be reproduced from the prediction record.
    """

    if decision.state == "assessed":
        names = [item.display_name for item in decision.candidates]
        if len(names) == 1:
            match = names[0]
        else:
            match = ", ".join(names[:-1]) + f" or {names[-1]}"
        text = (
            f"The image may be consistent with {match}. "
            f"The result is uncertain; use it only as a prompt for a closer look. "
            f"{NOT_A_DIAGNOSIS} A clearer photo or an expert review can help."
        )
        text, blocked = _safe(text)
        return Explanation(
            title="Photo assessment",
            text=text,
            next_steps=("add_context", "request_review", "read_advisory"),
            blocked=blocked,
        )

    reason = decision.reason_code
    if reason == "quality_gate_failed":
        flag = quality.result if quality is not None else "no_plant"
        text = _QUALITY_TEXT.get(flag, "The image did not pass the quality check.")
        text = f"{text} {NOT_A_DIAGNOSIS} Retake the photo to try again."
        next_steps: tuple[str, ...] = ("retake",)
    elif reason == "unsupported_crop":
        crops = ", ".join(supported_crops)
        text = (
            f"{_REASON_TEXT['unsupported_crop']} Supported crops: {crops}. "
            f"{NOT_A_DIAGNOSIS} You can change the crop or request expert review."
        )
        next_steps = ("change_crop", "request_review")
    else:
        body = _REASON_TEXT.get(reason or "", "The image could not be assessed reliably.")
        text = f"{body} {NOT_A_DIAGNOSIS} Retake the photo or request expert review."
        next_steps = ("retake", "request_review")

    text, blocked = _safe(text)
    return Explanation(
        title="Photo assessment",
        text=text,
        next_steps=next_steps,
        blocked=blocked,
    )

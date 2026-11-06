"""Prohibited-content validator (spec 07 §2, FR-07-02).

The validator is code with tests. Publication is blocked while any pattern
matches. It deliberately errs on the conservative side: an advisory that needs
unusual wording must be reworded, not exempted.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from app.modules.advisories.models import AdvisoryDraft


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    field: str
    match: str
    message: str


class AdvisoryContentRejected(ValueError):
    """Raised when advisory content contains a prohibited pattern."""

    def __init__(self, issues: Iterable[ValidationIssue]) -> None:
        self.issues = tuple(issues)
        self.codes = tuple(sorted({issue.code for issue in self.issues}))
        super().__init__(f"advisory content rejected: {', '.join(self.codes)}")


_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "product_name",
        re.compile(
            r"\b(glyphosate|chlorpyrifos|mancozeb|carbendazim|imidacloprid|"
            r"cypermethrin|profenofos|monocrotophos|endosulfan|paraquat)\b",
            re.IGNORECASE,
        ),
        "A named pesticide active ingredient is not allowed.",
    ),
    (
        "chemical_product",
        re.compile(
            r"\b(pesticide|insecticide|fungicide|herbicide|nematicide|rodenticide|"
            r"fertiliser|fertilizer)\b",
            re.IGNORECASE,
        ),
        "Chemical product classes are not allowed in advisory content.",
    ),
    (
        "dose",
        re.compile(
            r"\b\d+(\.\d+)?\s*(mg|g|kg|ml|cc|l|litre|liter|%)\s*(/|per)\s*"
            r"(l|litre|liter|kg|acre|hectare|ha)\b",
            re.IGNORECASE,
        ),
        "Dose or concentration instructions are not allowed.",
    ),
    (
        "dose_amount",
        re.compile(r"\b\d+(\.\d+)?\s*(mg|g|kg|ml|cc)\b", re.IGNORECASE),
        "Product amounts are not allowed in advisory content.",
    ),
    (
        "mixture",
        re.compile(r"\b(tank[\s-]?mix|mix (it )?with|mixture of)\b", re.IGNORECASE),
        "Mixture instructions are not allowed.",
    ),
    (
        "application_interval",
        re.compile(
            r"\b(spray|apply|application)\b.{0,40}\b(every|within|after)\b.{0,20}"
            r"\b\d+\s*(day|days|week|weeks|hour|hours)\b",
            re.IGNORECASE,
        ),
        "Application intervals are not allowed.",
    ),
    (
        "pre_harvest_interval",
        re.compile(r"\b(pre[\s-]?harvest interval|phi)\b", re.IGNORECASE),
        "Pre-harvest interval language is not allowed.",
    ),
    (
        "legal_use_claim",
        re.compile(r"\b(approved|registered|licensed)\s+for\s+use\b", re.IGNORECASE),
        "Legal-use claims are not allowed.",
    ),
    (
        "guarantee",
        re.compile(
            r"\b(will prevent|guaranteed|guarantees|assured to|will eliminate)\b",
            re.IGNORECASE,
        ),
        "Guarantees are not allowed.",
    ),
    (
        "diagnosis_claim",
        re.compile(
            r"\b(?:confirmed diagnosis|this confirms|definitely)\b|\b100\s?%",
            re.IGNORECASE,
        ),
        "Diagnostic claims are not allowed.",
    ),
    (
        "outbreak_claim",
        re.compile(r"\b(outbreak confirmed|confirmed outbreak)\b", re.IGNORECASE),
        "Outbreak-confirmation claims are not allowed.",
    ),
)


def _matches(field: str, text: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for code, pattern, message in _PATTERNS:
        for match in pattern.finditer(text):
            issues.append(
                ValidationIssue(
                    code=code,
                    field=field,
                    match=match.group(0)[:80],
                    message=message,
                )
            )
    return issues


def find_prohibited_matches(field: str, text: str) -> list[ValidationIssue]:
    """Expose the pattern check for tests and for rendered alert messages."""

    return _matches(field, text)


def validate_advisory(draft: AdvisoryDraft) -> tuple[ValidationIssue, ...]:
    """Return every issue in a draft. An empty tuple means publishable content."""

    issues: list[ValidationIssue] = []
    issues.extend(_matches("title", draft.title))
    for name, value in draft.body.model_dump().items():
        issues.extend(_matches(f"body.{name}", value))
    issues.extend(_matches("source", draft.source))

    if "not a diagnosis" not in draft.body.what_not_to_assume.lower():
        issues.append(
            ValidationIssue(
                code="missing_not_a_diagnosis",
                field="body.what_not_to_assume",
                match="",
                message="The 'what not to assume' section must state that this is not a diagnosis.",
            )
        )
    return tuple(issues)


def require_valid_advisory(draft: AdvisoryDraft) -> None:
    issues = validate_advisory(draft)
    if issues:
        raise AdvisoryContentRejected(issues)

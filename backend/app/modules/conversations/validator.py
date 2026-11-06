"""Deterministic content-safety validator for assistant replies (spec 08 CHAT-10).

The chat may only return template text built from the approved non-chemical
action set (scouting, monitoring, sanitation, crop management, escalation).
This module is the server-side gate that runs before any assistant message is
stored. It is a denylist and deliberately fail-closed: a reply that mentions a
chemical product, a dose, a mixture, an application interval or a spray
instruction is withheld rather than softened. The validator never rewrites text
and never calls a model.

The version is recorded on the ``validator_rejected`` audit event so a withheld
reply can be traced to the exact rule set that blocked it. The matched text is
not stored; only the rule categories are.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

VALIDATOR_VERSION = "chat-safety-0.1"


def _term_pattern(*terms: str) -> re.Pattern[str]:
    """Build one case-insensitive word-bounded pattern from plain terms."""

    alternatives = "|".join(r"\s+".join(re.escape(part) for part in term.split()) for term in terms)
    return re.compile(rf"\b(?:{alternatives})\b", re.IGNORECASE)


_TERM_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "chemical_product",
        _term_pattern(
            # Product classes. Any mention is out of scope for a v1 reply.
            "pesticide",
            "pesticides",
            "herbicide",
            "herbicides",
            "fungicide",
            "fungicides",
            "insecticide",
            "insecticides",
            "acaricide",
            "acaricides",
            "nematicide",
            "nematicides",
            "molluscicide",
            "molluscicides",
            "rodenticide",
            "rodenticides",
            "fumigant",
            "fumigants",
            "fertilizer",
            "fertilizers",
            "fertiliser",
            "fertilisers",
            # Common active ingredients and named products.
            "chlorothalonil",
            "mancozeb",
            "carbendazim",
            "thiophanate-methyl",
            "azoxystrobin",
            "propiconazole",
            "tebuconazole",
            "difenoconazole",
            "hexaconazole",
            "metalaxyl",
            "copper oxychloride",
            "copper hydroxide",
            "bordeaux mixture",
            "streptocycline",
            "streptomycin",
            "cypermethrin",
            "imidacloprid",
            "chlorpyrifos",
            "dimethoate",
            "malathion",
            "lambda-cyhalothrin",
            "deltamethrin",
            "glyphosate",
            "paraquat",
            "atrazine",
            "pendimethalin",
            "2,4-D",
            "neem oil",
            "azadirachtin",
            "abamectin",
            "spinosad",
            "emamectin",
            "fipronil",
            "thiamethoxam",
            "acetamiprid",
            "carbaryl",
            "monocrotophos",
            "profenofos",
            "quinalphos",
            "triazophos",
            "phorate",
            "carbofuran",
            "urea",
        ),
    ),
    ("dosage", _term_pattern("dose", "doses", "dosage", "dosages")),
    (
        "dosage",
        re.compile(
            r"\b\d+(?:\.\d+)?\s*(?:mg|g|kg|ml|l)\s*(?:/|per)\s*"
            r"(?:l|litre|liter|ha|hectare|acre)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "mixture",
        re.compile(
            r"\b(?:tank[\s-]?mix(?:es|ing)?|mixtures?|mix(?:ed|ing)?\s+with|"
            r"combine\s+with)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "application_interval",
        re.compile(
            r"\b(?:pre[\s-]?harvest|re[\s-]?entry|waiting|withholding)\s+"
            r"(?:interval|period)\b|\b(?:spray|application)\s+(?:interval|schedule)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "application_instruction",
        re.compile(
            r"\b(?:spray|sprays|spraying|fumigate|fumigating|fumigation|"
            r"drench|drenching)\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of one validation pass.

    ``categories`` holds rule names only, never the matched text, so the result
    is safe to place on an audit event.
    """

    allowed: bool
    version: str
    categories: tuple[str, ...] = ()


def validate_reply(*texts: str | None) -> ValidationResult:
    """Validate every user-visible string in an assistant reply.

    Pass the reply text, the assessment reason and any candidate display names.
    Empty or whitespace-only input is allowed: there is nothing to leak.
    """

    haystack = "\n".join(text for text in texts if text)
    if not haystack.strip():
        return ValidationResult(allowed=True, version=VALIDATOR_VERSION)

    categories = tuple(
        sorted({category for category, pattern in _TERM_RULES if pattern.search(haystack)})
    )
    return ValidationResult(
        allowed=not categories,
        version=VALIDATOR_VERSION,
        categories=categories,
    )

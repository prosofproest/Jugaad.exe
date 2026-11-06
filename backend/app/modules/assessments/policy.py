"""Versioned triage policy.

A policy is deployment configuration, not source code. It carries the crop
list, class taxonomy and the D8 operating point (per-class ``tau_c``, margin,
entropy and OOD threshold). Nothing here supplies a default value: an absent
or partial policy fails closed instead of inventing a threshold (D8/R6).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PolicyError(ValueError):
    """Raised when a triage policy is missing, unreadable or inconsistent."""


class ClassDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str = Field(min_length=1, max_length=80)
    display_name: str = Field(min_length=1, max_length=120)
    tau_c: float = Field(gt=0, lt=1)


class DecisionThresholds(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    margin: float = Field(ge=0, le=1)
    entropy: float = Field(gt=0, le=1)
    ood_max: float = Field(ge=0, le=1)
    ood_enabled: bool = True


class ConfidenceBandThresholds(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    high_min: float = Field(ge=0, le=1)
    medium_min: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def _ordered(self) -> ConfidenceBandThresholds:
        if self.high_min <= self.medium_min:
            raise ValueError("high_min must be greater than medium_min")
        return self


class QualityThresholds(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str = Field(min_length=1, max_length=80)
    min_width: int = Field(gt=0)
    min_height: int = Field(gt=0)
    min_laplacian_variance: float = Field(gt=0)
    min_mean_luma: float = Field(ge=0, lt=255)
    max_mean_luma: float = Field(gt=0, le=255)
    max_clipped_fraction: float = Field(ge=0, lt=1)
    min_plant_presence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def _luma_range(self) -> QualityThresholds:
        if self.min_mean_luma >= self.max_mean_luma:
            raise ValueError("min_mean_luma must be lower than max_mean_luma")
        return self


class TriagePolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = Field(min_length=1, max_length=40)
    taxonomy_version: str = Field(min_length=1, max_length=80)
    default_model_version: str = Field(min_length=1, max_length=120)
    # Test policies declare their provenance so a fixture can never be mistaken
    # for a validated deployment configuration.
    fixture_kind: Literal["synthetic_unit_test"] | None = None
    is_demo: bool = False
    supported_crops: list[str] = Field(min_length=1)
    classes: list[ClassDefinition] = Field(min_length=2)
    decision: DecisionThresholds
    confidence_bands: ConfidenceBandThresholds | None = None
    quality: QualityThresholds
    max_candidates: int = Field(default=3, ge=1, le=3)

    @model_validator(mode="after")
    def _unique(self) -> TriagePolicy:
        labels = [item.label for item in self.classes]
        if len(set(labels)) != len(labels):
            raise ValueError("class labels must be unique")
        crops = self.supported_crops
        if len(set(crops)) != len(crops):
            raise ValueError("supported_crops must be unique")
        if self.fixture_kind is not None and not self.is_demo:
            raise ValueError("a synthetic fixture policy must set is_demo=true")
        return self

    def class_definition(self, label: str) -> ClassDefinition:
        for item in self.classes:
            if item.label == label:
                return item
        raise KeyError(label)

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(item.label for item in self.classes)


def load_policy_file(path: str | Path) -> TriagePolicy:
    """Load a policy JSON file. Any failure is explicit, never defaulted."""

    file_path = Path(path)
    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise PolicyError(f"triage policy not found: {file_path}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise PolicyError(f"triage policy unreadable: {file_path}") from error
    return load_policy_dict(raw)


def load_policy_dict(raw: object) -> TriagePolicy:
    try:
        return TriagePolicy.model_validate(raw)
    except Exception as error:  # pydantic ValidationError
        raise PolicyError(f"invalid triage policy: {error}") from error

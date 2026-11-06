"""Model registry and the serving approval gate.

A model is servable only when its registry row is ``approved``, its artefact
checksum matches and its taxonomy/calibration versions are consistent with the
request. Training or evaluation status alone never promotes a model.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RegistryError(ValueError):
    """Raised when the registry cannot be loaded."""


class ModelNotApproved(RegistryError):
    """Raised when a model may not be served. Carries a machine code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class RegistryEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    model_version: str = Field(min_length=1, max_length=120)
    status: Literal["trained", "evaluated", "approved", "retired", "rejected"]
    artefact_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    taxonomy_version: str = Field(min_length=1, max_length=80)
    preprocessing_version: str = Field(min_length=1, max_length=80)
    calibration_version: str | None = None
    calibration_approved: bool = False
    # Metrics are optional and must carry provenance. A synthetic fixture is
    # never allowed to look like a field result.
    metrics: dict[str, float] | None = None
    metric_provenance: Literal["synthetic_fixture", "validation", "field_test"] | None = None
    is_demo: bool = False
    created_at: datetime
    approved_at: datetime | None = None

    @model_validator(mode="after")
    def _consistency(self) -> RegistryEntry:
        if self.calibration_approved and not self.calibration_version:
            raise ValueError("calibration_approved requires calibration_version")
        if self.metrics is not None and self.metric_provenance is None:
            raise ValueError("metrics require metric_provenance")
        if self.metric_provenance == "synthetic_fixture" and not self.is_demo:
            raise ValueError("synthetic fixture metrics must set is_demo=true")
        if self.status == "approved" and self.approved_at is None:
            raise ValueError("approved entries require approved_at")
        return self


class ModelRegistry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = Field(default="1.0", min_length=1, max_length=40)
    models: list[RegistryEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_versions(self) -> ModelRegistry:
        versions = [entry.model_version for entry in self.models]
        if len(set(versions)) != len(versions):
            raise ValueError("model_version must be unique")
        return self

    def find(self, model_version: str) -> RegistryEntry | None:
        for entry in self.models:
            if entry.model_version == model_version:
                return entry
        return None

    def require_servable(
        self,
        model_version: str,
        *,
        taxonomy_version: str,
        calibration_version: str | None = None,
        base_dir: Path | None = None,
    ) -> RegistryEntry:
        """Return the entry only if every serving precondition holds."""

        entry = self.find(model_version)
        if entry is None:
            raise ModelNotApproved("unknown_model_version")
        if entry.status == "retired":
            raise ModelNotApproved("model_retired")
        if entry.status != "approved":
            raise ModelNotApproved("model_not_approved")
        if entry.taxonomy_version != taxonomy_version:
            raise ModelNotApproved("taxonomy_version_mismatch")
        if entry.calibration_approved:
            if not calibration_version:
                raise ModelNotApproved("calibration_version_required")
            if entry.calibration_version != calibration_version:
                raise ModelNotApproved("calibration_version_mismatch")

        root = base_dir if base_dir is not None else Path.cwd()
        artefact = Path(entry.artefact_path)
        if not artefact.is_absolute():
            artefact = root / artefact
        if not artefact.is_file():
            raise ModelNotApproved("artefact_missing")
        digest = hashlib.sha256(artefact.read_bytes()).hexdigest()
        if digest != entry.sha256:
            raise ModelNotApproved("artefact_checksum_mismatch")
        return entry


def load_registry_file(path: str | Path) -> ModelRegistry:
    file_path = Path(path)
    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RegistryError(f"model registry not found: {file_path}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise RegistryError(f"model registry unreadable: {file_path}") from error
    try:
        return ModelRegistry.model_validate(raw)
    except Exception as error:
        raise RegistryError(f"invalid model registry: {error}") from error

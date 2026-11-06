# model_registry.py
"""Simple in‑memory model registry used by the inference pipeline.

During development this is a lightweight placeholder; in production it can be
replaced with a DB‑backed implementation or a Model Registry service.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ModelInfo:
    """Metadata for a registered model version."""
    name: str
    version: str
    checksum: str
    approved: bool
    created_at: datetime
    path: str  # location of the model artefact

    @property
    def identifier(self) -> str:
        return f"{self.name}:{self.version}"


class ModelRegistry:
    """Very small registry that keeps model entries in a dict.

    The API mirrors what the rest of the codebase expects:
    * ``register_model`` – add a new model (checksum is computed automatically).
    * ``get_latest_approved`` – retrieve the most recent approved version for a name.
    * ``list_models`` – optional helper for debugging.
    """

    def __init__(self) -> None:
        self._store: Dict[str, List[ModelInfo]] = {}

    @staticmethod
    def _calc_checksum(file_path: str) -> str:
        """Return a SHA256 hex digest for the given file.
        In a real deployment you would stream the file; here we read it whole –
        sufficient for the placeholder implementation.
        """
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            return hashlib.sha256(data).hexdigest()
        except FileNotFoundError:
            return ""

    def register_model(
        self,
        name: str,
        version: str,
        path: str,
        approved: bool = False,
    ) -> ModelInfo:
        """Add a model entry to the registry.

        Args:
            name: Logical model name (e.g. "disease‑detector").
            version: Semantic version string.
            path: Filesystem path to the artefact.
            approved: Whether the model is approved for production use.
        """
        checksum = self._calc_checksum(path)
        info = ModelInfo(
            name=name,
            version=version,
            checksum=checksum,
            approved=approved,
            created_at=datetime.utcnow(),
            path=path,
        )
        self._store.setdefault(name, []).append(info)
        # Keep list sorted newest‑first for quick lookup
        self._store[name].sort(key=lambda m: m.created_at, reverse=True)
        return info

    def get_latest_approved(self, name: str) -> Optional[ModelInfo]:
        """Return the most recent *approved* model entry for ``name``.
        Returns ``None`` if no approved model exists.
        """
        for model in self._store.get(name, []):
            if model.approved:
                return model
        return None

    def list_models(self, name: Optional[str] = None) -> List[ModelInfo]:
        """Utility to list stored models – helpful for debugging or admin UI."""
        if name:
            return list(self._store.get(name, []))
        # Flatten all entries
        all_models: List[ModelInfo] = []
        for models in self._store.values():
            all_models.extend(models)
        return all_models

# Global singleton used by the application
registry = ModelRegistry()

# Example registration (can be removed or replaced by startup code)
# registry.register_model("disease‑detector", "0.1.0", "path/to/model.pt", approved=True)


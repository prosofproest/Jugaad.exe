"""Feature-vector contract for the ML scaffold.

The real image feature extractor is **not implemented**. A dataset must supply
pre-extracted embedding vectors produced by a documented, versioned extractor;
this module only validates that contract so training and evaluation cannot
silently consume malformed or non-finite inputs.

The synthetic fixture uses ``synthetic-features-v1`` and four numeric
dimensions. That version identifies fixture geometry, not an image model.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

FEATURE_CONTRACT_VERSION = "synthetic-features-v1"
FEATURE_DIM = 4


class FeatureError(ValueError):
    """Raised when a feature vector does not satisfy the contract."""


def validate_feature_vector(
    values: Sequence[object],
    *,
    expected_dim: int = FEATURE_DIM,
    context: str = "feature vector",
) -> tuple[float, ...]:
    """Return ``values`` as finite floats, or raise ``FeatureError``."""

    if expected_dim <= 0:
        raise FeatureError("expected_dim must be positive")
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise FeatureError(f"{context} must be a sequence of numbers")
    if len(values) != expected_dim:
        raise FeatureError(f"{context} must contain exactly {expected_dim} values")

    result: list[float] = []
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise FeatureError(f"{context}[{index}] must be a number")
        number = float(value)
        if not math.isfinite(number):
            raise FeatureError(f"{context}[{index}] must be finite")
        result.append(number)
    return tuple(result)

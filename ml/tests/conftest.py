from __future__ import annotations

from pathlib import Path

import pytest

ML_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ML_ROOT / "fixtures"
CONTRACT = ML_ROOT / "contract"


@pytest.fixture
def manifest_path() -> Path:
    return FIXTURES / "synthetic_manifest.json"

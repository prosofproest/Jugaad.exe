"""Locate the sibling backend package that owns the shared Gate 3 code.

The scaffold deliberately reuses the backend's evaluation and registry modules
instead of duplicating safety-critical logic. Tests add ``../backend`` through
``pyproject.toml``; this helper makes the CLI work from ``ml/`` as well.
"""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_backend_on_path() -> Path:
    backend_root = Path(__file__).resolve().parents[2] / "backend"
    if not (backend_root / "app").is_dir():
        raise RuntimeError(f"backend package not found under {backend_root}")
    location = str(backend_root)
    if location not in sys.path:
        sys.path.insert(0, location)
    return backend_root

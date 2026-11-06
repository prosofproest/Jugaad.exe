"""Regenerate the committed synthetic fixture files.

Run from the repository root:

    backend\\.venv\\Scripts\\python ml\\fixtures\\build_synthetic_dataset.py

The output is deterministic; ``ml/tests/test_synthetic_fixture.py`` checks that
the committed files match a fresh build byte for byte.
"""

from __future__ import annotations

import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[1]
if str(ML_ROOT) not in sys.path:
    sys.path.insert(0, str(ML_ROOT))

from pest_ml.synthetic import write_dataset  # noqa: E402

if __name__ == "__main__":
    for path in write_dataset(Path(__file__).resolve().parent):
        print(path)

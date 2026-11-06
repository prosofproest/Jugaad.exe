"""Video reading module (spec 09).

A short clip is a capture format for the existing photo-assessment pipeline, not
a new model and not a new diagnostic output. The shipped detector is a
deterministic motion-region heuristic and the tracker is a dependency-light
ByteTrack-style association; both are visibly demo-labelled until a validated
model exists (D1/D2, D15).
"""

from app.modules.video import orm  # noqa: F401  (registers the tables)

__all__ = ["orm"]

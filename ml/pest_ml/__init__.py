"""Reproducible ML scaffold for the image-triage pipeline.

This package trains and evaluates a deterministic toy baseline on an
explicitly synthetic fixture. It is machinery verification only: it does not
ship a trained image model, a real dataset, an operating point or a
performance claim.

The real image feature extractor, dataset acquisition and operating-point
decision are still outstanding. See ``ml/README.md``.
"""

from .manifest import DatasetItem, DatasetManifest, ManifestError, load_manifest
from .splits import SplitAssignment, SplitError, assign_splits

__all__ = [
    "DatasetItem",
    "DatasetManifest",
    "ManifestError",
    "SplitAssignment",
    "SplitError",
    "assign_splits",
    "load_manifest",
]

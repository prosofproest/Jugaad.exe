"""Assistive photo-assessment (image triage) module.

The module implements the safety-critical part of Phase 3: the quality gate,
the D8 abstention decision function, calibration, the model registry and the
append-only prediction record. It deliberately contains no crop list, class
taxonomy or numeric operating point. Those are deployment configuration that
must be supplied only after the relevant decisions are recorded.
"""

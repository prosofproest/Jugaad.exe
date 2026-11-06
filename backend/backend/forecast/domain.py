"""Closed sets and domain errors for the forecast track.

The sets mirror ``feature-specs/06-forecast-and-risk-map.md`` and
``05-data-layer.md``. They are ``str`` enums so they serialise directly into
API payloads and SQLite text columns without a translation layer.
"""

from __future__ import annotations

from enum import Enum


class RiskBand(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    URGENT = "urgent"
    INSUFFICIENT_DATA = "insufficient_data"


class Coverage(str, Enum):
    GOOD = "good"
    PARTIAL = "partial"
    LOW = "low"
    UNKNOWN = "unknown"


class ReasonCode(str, Enum):
    """Machine-readable explanation for a scored or no-score forecast."""

    OK = "ok"
    UNSUPPORTED_TARGET = "unsupported_target"
    TARGET_NOT_FORECAST_ELIGIBLE = "target_not_forecast_eligible"
    MODEL_NOT_APPROVED = "model_not_approved"
    BOUNDARY_MISMATCH = "boundary_mismatch"
    CALENDAR_MISSING = "calendar_missing"
    WEATHER_MISSING = "weather_missing"
    WEATHER_STALE = "weather_stale"
    WEATHER_INCOMPLETE = "weather_incomplete"
    COVERAGE_LOW = "coverage_low"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    CONFIRMED = "confirmed"
    PROBABLE = "probable"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    NEEDS_VISIT = "needs_visit"
    UNRESOLVED = "unresolved"


BAND_ORDER: dict[str, int] = {
    RiskBand.LOW.value: 0,
    RiskBand.MODERATE.value: 1,
    RiskBand.HIGH.value: 2,
    RiskBand.URGENT.value: 3,
}

# Coverage is deliberately not a numeric "risk": low coverage means "we do not
# know", never "the area is safe".
COVERAGE_ORDER: dict[str, int] = {
    Coverage.UNKNOWN.value: 0,
    Coverage.LOW.value: 1,
    Coverage.PARTIAL.value: 2,
    Coverage.GOOD.value: 3,
}


def coverage_band(score: float) -> Coverage:
    """Map a 0..1 coverage score to the published band.

    Thresholds are the D9 placeholder values stored in the versioned forecast
    config; this function only defines the bands, not the score itself.
    """

    if score >= 0.75:
        return Coverage.GOOD
    if score >= 0.50:
        return Coverage.PARTIAL
    return Coverage.LOW


class DomainError(Exception):
    """Base class for errors translated to HTTP only at the router edge."""

    code = "domain_error"
    http_status = 422

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class UnsupportedTargetError(DomainError):
    code = "unsupported_target"
    http_status = 422


class FeatureLeakageError(DomainError):
    """Raised when an input claims a timestamp after the forecast issue time."""

    code = "feature_leakage"
    http_status = 500


class AdvisoryContentError(DomainError):
    code = "advisory_content_rejected"
    http_status = 422

    def __init__(self, message: str, issues: list[dict[str, str]] | None = None) -> None:
        super().__init__(message)
        self.issues = issues or []


class PermissionDeniedError(DomainError):
    code = "permission_denied"
    http_status = 403


class NotFoundError(DomainError):
    code = "not_found"
    http_status = 404


class ConflictError(DomainError):
    code = "conflict"
    http_status = 409

"""Transparent agronomic rules baseline.

This is the day-one forecast model from the specification's model ladder: a
documented, versioned index built from weather thresholds and crop stage.
It is intentionally simple and inspectable. The weights and thresholds in the
shipped config are **provisional demonstration values**; they are not an
agronomic claim and must be replaced after local validation.

The scoring function is pure: the same feature payload and the same
``scoring`` block always produce the same band. That property is what makes a
stored forecast reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import BandThresholds, TargetRules

DRIVER_LABELS = {
    "wetness": "consecutive_wet_days",
    "temperature": "temperature_window",
    "humidity": "high_humidity",
    "crop_stage": "susceptible_crop_stage",
    "local_evidence": "local_verified_reports",
}

# Evidence is counted with a documented half-weight for neighbouring blocks so
# a single neighbouring report cannot dominate the local signal.
NEARBY_EVIDENCE_WEIGHT = 0.5
EVIDENCE_SATURATION = 3.0


@dataclass(frozen=True)
class RuleScore:
    score: float
    band: str
    components: dict[str, float]
    contributions: dict[str, float]
    drivers: list[str]
    rules_version: str
    confidence: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "band": self.band,
            "components": self.components,
            "contributions": self.contributions,
            "drivers": self.drivers,
            "rules_version": self.rules_version,
            "confidence": self.confidence,
        }


def _temperature_suitability(
    temperature_c: float,
    optimum: tuple[float, float],
    tolerance_c: float,
) -> float:
    low, high = optimum
    if low <= temperature_c <= high:
        return 1.0
    distance = low - temperature_c if temperature_c < low else temperature_c - high
    if tolerance_c <= 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - distance / tolerance_c))


def _crop_stage_factor(stage: str | None, susceptible_stages: tuple[str, ...]) -> float:
    if not stage:
        # A missing stage should normally be blocked by the calendar gate. Keep
        # the factor conservative if scoring is ever reached without one.
        return 0.0
    return 1.0 if stage in susceptible_stages else 0.35


def score_target(
    target: TargetRules,
    features: dict[str, Any],
    bands: BandThresholds,
    *,
    coverage: str,
    weather_completeness: float,
) -> RuleScore:
    weather = features.get("weather", {})
    pressure = features.get("pressure", {})
    crop = features.get("crop", {})

    days_observed = int(weather.get("days_observed", 0) or 0)
    high_humidity_days = int(weather.get("high_humidity_days", 0) or 0)
    max_wet_run = float(weather.get("max_consecutive_wet_days", 0) or 0)
    temp_mean = float(weather.get("temp_mean_c", 0) or 0)

    wetness = (
        min(max_wet_run / target.consecutive_wet_days_target, 1.0)
        if target.consecutive_wet_days_target > 0
        else 0.0
    )
    temperature = _temperature_suitability(
        temp_mean, target.temperature_optimum_c, target.temperature_tolerance_c
    )
    humidity = (
        min((high_humidity_days / days_observed) / 0.60, 1.0)
        if days_observed > 0
        else 0.0
    )
    crop_stage = _crop_stage_factor(crop.get("stage"), target.susceptible_stages)
    local = float(pressure.get("verified_reports_local", 0) or 0)
    nearby = float(pressure.get("verified_reports_nearby", 0) or 0)
    evidence = min(
        (local + NEARBY_EVIDENCE_WEIGHT * nearby) / EVIDENCE_SATURATION, 1.0
    )

    components = {
        "wetness": round(wetness, 6),
        "temperature": round(temperature, 6),
        "humidity": round(humidity, 6),
        "crop_stage": round(crop_stage, 6),
        "local_evidence": round(evidence, 6),
    }
    contributions = {
        name: round(target.weights.get(name, 0.0) * value, 6)
        for name, value in components.items()
    }
    score = round(sum(contributions.values()), 6)

    drivers = sorted(
        (
            (DRIVER_LABELS[name], contributions[name])
            for name, value in components.items()
            if value >= 0.5 and contributions[name] > 0
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    driver_labels = [label for label, _ in drivers[:3]]

    return RuleScore(
        score=score,
        band=bands.band_for(score).value,
        components=components,
        contributions=contributions,
        drivers=driver_labels,
        rules_version=target.rules_version,
        confidence=_confidence_for(coverage, weather_completeness),
    )


def _confidence_for(coverage: str, weather_completeness: float) -> str:
    """Qualitative confidence. Never a percentage; calibration is not approved.

    The maximum is ``medium`` while the config remains uncalibrated. A future
    approved calibration may add ``high`` through an explicit config change.
    """

    if coverage == "good" and weather_completeness >= 0.85:
        return "medium"
    if coverage in ("good", "partial"):
        return "low"
    return "none"


def rescore_from_features(feature_payload: dict[str, Any]) -> RuleScore:
    """Recompute a band from a stored feature snapshot.

    The snapshot carries the exact target rules and band thresholds used at
    issue time. This function never reads the current config, so editing the
    config later cannot rewrite history.
    """

    scoring = feature_payload["scoring"]
    target = TargetRules.from_dict(scoring["target"])
    bands = BandThresholds(
        moderate=scoring["bands"]["moderate"],
        high=scoring["bands"]["high"],
        urgent=scoring["bands"]["urgent"],
        approval_status=scoring["bands"].get("approval_status", "unapproved"),
    )
    coverage = feature_payload.get("coverage", {}).get("band", "unknown")
    completeness = float(
        feature_payload.get("coverage", {}).get("weather_completeness", 0.0)
    )
    return score_target(
        target,
        feature_payload,
        bands,
        coverage=coverage,
        weather_completeness=completeness,
    )

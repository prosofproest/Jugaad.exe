"""Versioned forecast configuration.

Every number that drives a forecast lives here, not inline in code. The
shipped demo config is explicitly ``status: demo`` and ``provisional: true``:
it can produce labelled demonstration output, but it cannot trigger an
operational alert and its band thresholds carry no agronomic approval.

The production rule from the specification is stricter: the model registry row
must be ``approved``. ``is_servable(allow_demo=False)`` enforces that.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .domain import RiskBand, UnsupportedTargetError

CONFIG_DIR = Path(__file__).parent / "configs"
DEFAULT_CONFIG_FILE = "forecast-rules-demo-0.1.json"


class ConfigError(ValueError):
    """Raised when a forecast config is missing or inconsistent."""


@dataclass(frozen=True)
class BandThresholds:
    moderate: float
    high: float
    urgent: float
    approval_status: str

    def band_for(self, score: float) -> RiskBand:
        if score >= self.urgent:
            return RiskBand.URGENT
        if score >= self.high:
            return RiskBand.HIGH
        if score >= self.moderate:
            return RiskBand.MODERATE
        return RiskBand.LOW

    def as_dict(self) -> dict[str, Any]:
        return {
            "moderate": self.moderate,
            "high": self.high,
            "urgent": self.urgent,
            "approval_status": self.approval_status,
        }


@dataclass(frozen=True)
class GateConfig:
    weather_freshness_hours: float
    min_active_reporters: int
    min_verified_reports: int
    min_weather_completeness: float
    coverage_window_days: int


@dataclass(frozen=True)
class CoverageConfig:
    weights: dict[str, float]
    good_threshold: float
    partial_threshold: float

    def band(self, score: float) -> str:
        if score >= self.good_threshold:
            return "good"
        if score >= self.partial_threshold:
            return "partial"
        return "low"


@dataclass(frozen=True)
class EventDefinition:
    event: str
    negative: str
    eligible_tiers: tuple[str, ...]
    never_eligible: tuple[str, ...]
    as_of_rule: str
    note: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "negative": self.negative,
            "eligible_tiers": list(self.eligible_tiers),
            "never_eligible": list(self.never_eligible),
            "as_of_rule": self.as_of_rule,
            "note": self.note,
        }


@dataclass(frozen=True)
class TargetRules:
    code: str
    display_name: str
    forecast_eligible: bool
    rules_version: str
    temperature_optimum_c: tuple[float, float]
    temperature_tolerance_c: float
    humidity_threshold_pct: float
    wet_day_rainfall_mm: float
    wet_day_humidity_pct: float
    consecutive_wet_days_target: float
    susceptible_stages: tuple[str, ...]
    weights: dict[str, float]

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "display_name": self.display_name,
            "forecast_eligible": self.forecast_eligible,
            "rules_version": self.rules_version,
            "temperature_optimum_c": list(self.temperature_optimum_c),
            "temperature_tolerance_c": self.temperature_tolerance_c,
            "humidity_threshold_pct": self.humidity_threshold_pct,
            "wet_day_rainfall_mm": self.wet_day_rainfall_mm,
            "wet_day_humidity_pct": self.wet_day_humidity_pct,
            "consecutive_wet_days_target": self.consecutive_wet_days_target,
            "susceptible_stages": list(self.susceptible_stages),
            "weights": dict(self.weights),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "TargetRules":
        return cls(
            code=raw["code"],
            display_name=raw.get("display_name", raw["code"]),
            forecast_eligible=bool(raw["forecast_eligible"]),
            rules_version=raw["rules_version"],
            temperature_optimum_c=tuple(
                float(x) for x in raw["temperature_optimum_c"]
            ),
            temperature_tolerance_c=float(raw["temperature_tolerance_c"]),
            humidity_threshold_pct=float(raw["humidity_threshold_pct"]),
            wet_day_rainfall_mm=float(raw["wet_day_rainfall_mm"]),
            wet_day_humidity_pct=float(raw["wet_day_humidity_pct"]),
            consecutive_wet_days_target=float(
                raw["consecutive_wet_days_target"]
            ),
            susceptible_stages=tuple(raw["susceptible_stages"]),
            weights={str(k): float(v) for k, v in raw["weights"].items()},
        )


@dataclass(frozen=True)
class ForecastConfig:
    model_version: str
    status: str
    is_demo: bool
    provisional: bool
    approval_note: str
    approved_by: str | None
    approved_at: str | None
    review_date: str | None
    spatial_level: str
    boundary_version: str
    horizon_days: int
    issue_cadence: str
    gates: GateConfig
    coverage: CoverageConfig
    bands: BandThresholds
    suppression_min_count: int
    event_definition: EventDefinition
    targets: dict[str, TargetRules]
    config_hash: str
    raw: dict[str, Any]

    # ------------------------------------------------------------------ load
    @classmethod
    def load(cls, path: str | Path | None = None) -> "ForecastConfig":
        config_path = Path(path) if path else CONFIG_DIR / DEFAULT_CONFIG_FILE
        if not config_path.exists():
            raise ConfigError(f"forecast config not found: {config_path}")
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ForecastConfig":
        required = [
            "model_version",
            "status",
            "spatial_level",
            "boundary_version",
            "horizon_days",
            "gates",
            "coverage",
            "bands",
            "event_definition",
            "targets",
        ]
        missing = [key for key in required if key not in raw]
        if missing:
            raise ConfigError(f"forecast config missing keys: {', '.join(missing)}")

        gates = raw["gates"]
        coverage = raw["coverage"]
        bands = raw["bands"]
        event = raw["event_definition"]

        targets: dict[str, TargetRules] = {}
        for code, item in raw["targets"].items():
            try:
                weights = {str(k): float(v) for k, v in item["weights"].items()}
                total = sum(weights.values())
                if abs(total - 1.0) > 1e-6:
                    raise ConfigError(
                        f"target {code}: weights must sum to 1.0, got {total}"
                    )
                targets[code] = TargetRules(
                    code=code,
                    display_name=item.get("display_name", code),
                    forecast_eligible=bool(item["forecast_eligible"]),
                    rules_version=item["rules_version"],
                    temperature_optimum_c=tuple(
                        float(x) for x in item["temperature_optimum_c"]
                    ),
                    temperature_tolerance_c=float(item["temperature_tolerance_c"]),
                    humidity_threshold_pct=float(item["humidity_threshold_pct"]),
                    wet_day_rainfall_mm=float(item["wet_day_rainfall_mm"]),
                    wet_day_humidity_pct=float(item["wet_day_humidity_pct"]),
                    consecutive_wet_days_target=float(
                        item["consecutive_wet_days_target"]
                    ),
                    susceptible_stages=tuple(item["susceptible_stages"]),
                    weights=weights,
                )
            except KeyError as exc:
                raise ConfigError(f"target {code}: missing key {exc}") from exc

        canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        return cls(
            model_version=raw["model_version"],
            status=raw["status"],
            is_demo=bool(raw.get("is_demo", raw["status"] == "demo")),
            provisional=bool(raw.get("provisional", False)),
            approval_note=raw.get("approval_note", ""),
            approved_by=raw.get("approved_by"),
            approved_at=raw.get("approved_at"),
            review_date=raw.get("review_date"),
            spatial_level=raw["spatial_level"],
            boundary_version=raw["boundary_version"],
            horizon_days=int(raw["horizon_days"]),
            issue_cadence=raw.get("issue_cadence", "daily"),
            gates=GateConfig(
                weather_freshness_hours=float(gates["weather_freshness_hours"]),
                min_active_reporters=int(gates["min_active_reporters"]),
                min_verified_reports=int(gates["min_verified_reports"]),
                min_weather_completeness=float(gates["min_weather_completeness"]),
                coverage_window_days=int(gates["coverage_window_days"]),
            ),
            coverage=CoverageConfig(
                weights={str(k): float(v) for k, v in coverage["weights"].items()},
                good_threshold=float(coverage["good_threshold"]),
                partial_threshold=float(coverage["partial_threshold"]),
            ),
            bands=BandThresholds(
                moderate=float(bands["moderate"]),
                high=float(bands["high"]),
                urgent=float(bands["urgent"]),
                approval_status=str(bands.get("approval_status", "unapproved")),
            ),
            suppression_min_count=int(
                raw.get("suppression", {}).get("min_count", 5)
            ),
            event_definition=EventDefinition(
                event=str(event["event"]),
                negative=str(event["negative"]),
                eligible_tiers=tuple(event["eligible_tiers"]),
                never_eligible=tuple(event["never_eligible"]),
                as_of_rule=str(event["as_of_rule"]),
                note=str(event.get("note", "")),
            ),
            targets=targets,
            config_hash=digest,
            raw=raw,
        )

    # -------------------------------------------------------------- helpers
    def target(self, code: str) -> TargetRules:
        try:
            return self.targets[code]
        except KeyError as exc:
            raise UnsupportedTargetError(
                f"target is not in the configured catalogue: {code}"
            ) from exc

    def is_servable(self, *, allow_demo: bool) -> bool:
        """A forecast may be generated only with an approved registry row.

        Demo configs are explicitly opt-in and remain labelled downstream.
        """

        if self.status == "approved":
            return True
        return self.is_demo and allow_demo

    def scoring_block(self, target: TargetRules) -> dict[str, Any]:
        """The exact scoring inputs captured in a feature snapshot.

        Recomputing a stored forecast uses this block, so a later config edit
        cannot silently change a historical band.
        """

        return {
            "model_version": self.model_version,
            "config_hash": self.config_hash,
            "target": target.as_dict(),
            "bands": self.bands.as_dict(),
        }

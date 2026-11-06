"""Calibration utilities (D8).

Temperature scaling is fitted on a dedicated calibration split, separate from
the model-selection validation split and the frozen test set. The numbers this
module computes are diagnostics for an explicitly supplied dataset; it never
invents a floor, a split or a sample count.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Sequence

_EPSILON = 1e-12


class CalibrationError(ValueError):
    """Raised when calibration cannot be fitted or applied safely."""


class CalibrationNotApproved(CalibrationError):
    """Raised when a split is too small or inconsistent to support calibration."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def softmax(logits: Sequence[float]) -> list[float]:
    """Numerically stable softmax."""

    if not logits:
        raise CalibrationError("logits must not be empty")
    if any(not math.isfinite(value) for value in logits):
        raise CalibrationError("logits must be finite")
    peak = max(logits)
    exps = [math.exp(value - peak) for value in logits]
    total = sum(exps)
    return [value / total for value in exps]


@dataclass(frozen=True)
class CalibrationDiagnostics:
    n_samples: int
    nll: float
    brier: float
    ece: float
    n_bins: int


@dataclass(frozen=True)
class TemperatureCalibration:
    """A fitted temperature-scaling artefact.

    ``version`` and ``checksum`` identify the artefact that produced a
    prediction; both are stored on the append-only prediction row.
    """

    version: str
    temperature: float
    n_samples: int
    fitted_on: str
    data_fingerprint: str
    checksum: str

    def apply(self, logits: Sequence[float]) -> list[float]:
        if not math.isfinite(self.temperature) or self.temperature <= 0:
            raise CalibrationError("temperature must be finite and positive")
        scaled = [value / self.temperature for value in logits]
        return softmax(scaled)


def _negative_log_likelihood(logits: Sequence[Sequence[float]], labels: Sequence[int], temperature: float) -> float:
    total = 0.0
    for row, label in zip(logits, labels, strict=True):
        probs = softmax([value / temperature for value in row])
        total -= math.log(max(probs[label], _EPSILON))
    return total / len(logits)


def _golden_section(
    logits: Sequence[Sequence[float]],
    labels: Sequence[int],
    low: float,
    high: float,
    iterations: int = 80,
) -> float:
    """Minimise NLL over ``t = log(temperature)``. Deterministic."""

    golden = (math.sqrt(5.0) - 1.0) / 2.0
    a, b = low, high
    c = b - golden * (b - a)
    d = a + golden * (b - a)
    f_c = _negative_log_likelihood(logits, labels, math.exp(c))
    f_d = _negative_log_likelihood(logits, labels, math.exp(d))
    for _ in range(iterations):
        if f_c < f_d:
            b, d, f_d = d, c, f_c
            c = b - golden * (b - a)
            f_c = _negative_log_likelihood(logits, labels, math.exp(c))
        else:
            a, c, f_c = c, d, f_d
            d = a + golden * (b - a)
            f_d = _negative_log_likelihood(logits, labels, math.exp(d))
    return math.exp((a + b) / 2.0)


def fit_temperature(
    logits: Sequence[Sequence[float]],
    labels: Sequence[int],
    *,
    version: str,
    data_fingerprint: str,
    min_samples: int,
    fitted_on: str = "calibration_split",
    log_temperature_range: tuple[float, float] = (-4.0, 4.0),
) -> TemperatureCalibration:
    """Fit temperature scaling on a dedicated calibration split.

    ``min_samples`` is supplied by the deployment from the pre-registered D8
    procedure. If the split is smaller than that value, calibration is not
    approved and this function refuses to produce an artefact.
    """

    if not version:
        raise CalibrationError("calibration version is required")
    if not data_fingerprint:
        raise CalibrationError("calibration data fingerprint is required")
    if min_samples <= 0:
        raise CalibrationError("min_samples must be positive")
    if len(logits) != len(labels):
        raise CalibrationError("logits and labels must have equal length")
    if len(logits) < min_samples:
        raise CalibrationNotApproved("insufficient_calibration_samples")
    class_count = len(logits[0]) if logits else 0
    if class_count < 2:
        raise CalibrationError("at least two classes are required")
    for row in logits:
        if len(row) != class_count:
            raise CalibrationError("all logit rows must have equal length")
        if any(not math.isfinite(value) for value in row):
            raise CalibrationError("logits must be finite")
    for label in labels:
        if not isinstance(label, int) or not 0 <= label < class_count:
            raise CalibrationError("labels must index a class")

    low, high = log_temperature_range
    if not low < high:
        raise CalibrationError("invalid temperature search range")
    temperature = _golden_section(logits, labels, low, high)

    fingerprint = {
        "version": version,
        "temperature": round(temperature, 12),
        "n_samples": len(logits),
        "fitted_on": fitted_on,
        "data_fingerprint": data_fingerprint,
    }
    checksum = hashlib.sha256(
        json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return TemperatureCalibration(
        version=version,
        temperature=temperature,
        n_samples=len(logits),
        fitted_on=fitted_on,
        data_fingerprint=data_fingerprint,
        checksum=checksum,
    )


def calibration_diagnostics(
    probabilities: Sequence[Sequence[float]],
    labels: Sequence[int],
    *,
    n_bins: int = 10,
) -> CalibrationDiagnostics:
    """Report NLL, multiclass Brier and ECE for an explicitly supplied set.

    This is a diagnostic on real or synthetic fixtures. It is never a
    performance claim about a model.
    """

    if len(probabilities) != len(labels):
        raise CalibrationError("probabilities and labels must have equal length")
    if not probabilities:
        raise CalibrationError("at least one sample is required")
    if n_bins < 1:
        raise CalibrationError("n_bins must be positive")

    n_samples = len(probabilities)
    nll = 0.0
    brier = 0.0
    confidences: list[float] = []
    correctness: list[float] = []

    for row, label in zip(probabilities, labels, strict=True):
        if not row:
            raise CalibrationError("probability rows must not be empty")
        total = sum(row)
        if abs(total - 1.0) > 1e-6:
            raise CalibrationError("probability rows must sum to 1")
        if any(value < 0 or value > 1 for value in row):
            raise CalibrationError("probabilities must be in [0, 1]")
        if not 0 <= label < len(row):
            raise CalibrationError("labels must index a class")

        true_probability = row[label]
        nll -= math.log(max(true_probability, _EPSILON))
        brier += sum(
            (probability - (1.0 if index == label else 0.0)) ** 2
            for index, probability in enumerate(row)
        )
        top = max(range(len(row)), key=lambda index: row[index])
        confidences.append(row[top])
        correctness.append(1.0 if top == label else 0.0)

    ece = 0.0
    for bin_index in range(n_bins):
        lower = bin_index / n_bins
        upper = (bin_index + 1) / n_bins
        members = [
            index
            for index, confidence in enumerate(confidences)
            if lower <= confidence < upper or (bin_index == n_bins - 1 and confidence == 1.0)
        ]
        if not members:
            continue
        bin_confidence = sum(confidences[index] for index in members) / len(members)
        bin_accuracy = sum(correctness[index] for index in members) / len(members)
        ece += (len(members) / n_samples) * abs(bin_accuracy - bin_confidence)

    return CalibrationDiagnostics(
        n_samples=n_samples,
        nll=nll / n_samples,
        brier=brier / n_samples,
        ece=ece,
        n_bins=n_bins,
    )

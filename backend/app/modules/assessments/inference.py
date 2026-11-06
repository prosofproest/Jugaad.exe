"""Inference boundary with timeout, retry and safe failure.

No model is bundled in this repository. The adapter is injected by the
deployment; the default adapter refuses to answer. A missing or failing model
must produce a safe ``failed`` outcome, never a fabricated assessment.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from time import perf_counter
from typing import Protocol


class InferenceFailure(Exception):
    """A typed inference failure that the service can surface safely."""

    def __init__(self, code: str, *, retryable: bool = True) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class InferenceRequest:
    crop_id: str
    content_hash: str
    width: int
    height: int


@dataclass(frozen=True)
class InferenceOutput:
    logits: Mapping[str, float]
    ood_score: float
    model_version: str
    preprocessing_version: str


class InferenceAdapter(Protocol):
    def predict(self, request: InferenceRequest) -> InferenceOutput:
        """Return raw logits for every taxonomy label plus an OOD score."""


class NullInferenceAdapter:
    """Default adapter: no approved model is configured in this deployment."""

    def predict(self, request: InferenceRequest) -> InferenceOutput:
        raise InferenceFailure("inference_not_configured", retryable=False)


def _validate_output(output: InferenceOutput) -> None:
    if not output.logits:
        raise InferenceFailure("invalid_inference_output", retryable=False)
    for label, value in output.logits.items():
        if not isinstance(label, str) or not label:
            raise InferenceFailure("invalid_inference_output", retryable=False)
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise InferenceFailure("invalid_inference_output", retryable=False)
    if not isinstance(output.ood_score, (int, float)) or not math.isfinite(float(output.ood_score)):
        raise InferenceFailure("invalid_inference_output", retryable=False)
    if not 0.0 <= float(output.ood_score) <= 1.0:
        raise InferenceFailure("invalid_inference_output", retryable=False)
    if not output.model_version or not output.preprocessing_version:
        raise InferenceFailure("invalid_inference_output", retryable=False)


class InferenceRunner:
    """Run an adapter with a hard timeout and bounded retries."""

    def __init__(self, *, timeout_s: float = 5.0, max_attempts: int = 2) -> None:
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self._timeout_s = timeout_s
        self._max_attempts = max_attempts

    def run(
        self, adapter: InferenceAdapter, request: InferenceRequest
    ) -> tuple[InferenceOutput, float]:
        last_code = "inference_error"
        last_retryable = True

        for _ in range(self._max_attempts):
            pool = ThreadPoolExecutor(max_workers=1)
            started = perf_counter()
            future = pool.submit(adapter.predict, request)
            try:
                output = future.result(timeout=self._timeout_s)
                latency_ms = (perf_counter() - started) * 1000.0
                _validate_output(output)
                return output, latency_ms
            except FutureTimeout:
                last_code = "inference_timeout"
                last_retryable = True
            except InferenceFailure as error:
                last_code = error.code
                last_retryable = error.retryable
            except Exception:  # noqa: BLE001 - the boundary converts every failure
                last_code = "inference_error"
                last_retryable = True
            finally:
                # Do not wait for a hung worker; the caller has already decided
                # this attempt timed out.
                pool.shutdown(wait=False, cancel_futures=True)

        raise InferenceFailure(last_code, retryable=last_retryable)

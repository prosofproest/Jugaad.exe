"""Append-only prediction records.

The scaffold keeps records in memory, but the contract is the same one the
database will enforce: one row per run, no update or delete, and enough stored
detail (threshold set, OOD score, calibration and model versions, input
snapshot reference) to reproduce the abstention decision.
"""

from __future__ import annotations

from datetime import datetime
from threading import Lock

from pydantic import BaseModel, ConfigDict, Field

from app.modules.assessments.schemas import CandidateOut


class DuplicateAssessmentError(ValueError):
    """Raised when a client assessment id is appended twice."""


class PredictionRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    prediction_id: str
    client_assessment_id: str
    crop_id: str
    content_hash: str
    input_snapshot_ref: str

    state: str
    abstained: bool
    abstain_reason: str | None
    reason_text: str
    next_steps: tuple[str, ...]
    not_a_diagnosis: bool = True

    quality_result: str
    quality_flags: tuple[str, ...]
    quality_gate_version: str

    candidates: tuple[CandidateOut, ...] = ()
    confidence_band: str | None
    calibrated: bool
    calibration_version: str | None

    model_version: str
    taxonomy_version: str
    preprocessing_version: str | None
    score_kind: str
    scores: dict[str, float] | None
    decision_thresholds: dict
    ood_score: float | None

    latency_ms: float | None
    generated_at: datetime
    is_demo: bool


class InMemoryPredictionStore:
    """Append-only store with idempotency on ``client_assessment_id``."""

    def __init__(self) -> None:
        self._rows: dict[str, PredictionRecord] = {}
        self._by_client: dict[str, str] = {}
        self._lock = Lock()

    def append(self, record: PredictionRecord) -> PredictionRecord:
        with self._lock:
            if record.prediction_id in self._rows:
                raise DuplicateAssessmentError("duplicate prediction_id")
            existing = self._by_client.get(record.client_assessment_id)
            if existing is not None:
                raise DuplicateAssessmentError("duplicate client_assessment_id")
            self._rows[record.prediction_id] = record
            self._by_client[record.client_assessment_id] = record.prediction_id
            return record

    def find_by_client(self, client_assessment_id: str) -> PredictionRecord | None:
        with self._lock:
            prediction_id = self._by_client.get(client_assessment_id)
            if prediction_id is None:
                return None
            return self._rows[prediction_id]

    def get(self, prediction_id: str) -> PredictionRecord | None:
        with self._lock:
            return self._rows.get(prediction_id)

    def list(self, *, limit: int = 20, cursor: str | None = None) -> tuple[list[PredictionRecord], str | None]:
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        offset = 0
        if cursor is not None:
            try:
                offset = int(cursor)
            except ValueError as error:
                raise ValueError("invalid cursor") from error
            if offset < 0:
                raise ValueError("invalid cursor")
        with self._lock:
            newest_first = list(self._rows.values())[::-1]
        window = newest_first[offset : offset + limit]
        next_offset = offset + len(window)
        next_cursor = str(next_offset) if next_offset < len(newest_first) else None
        return window, next_cursor

    def count(self) -> int:
        with self._lock:
            return len(self._rows)

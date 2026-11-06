"""Assessment orchestration.

Order of safety checks:

1. crop support (no model call for an unsupported crop);
2. server quality gate (no model call for an unusable image);
3. registry approval, checksum and version consistency;
4. bounded inference;
5. calibration (or raw scores with qualitative output only);
6. the D8 decision function;
7. append-only persistence, then the user-facing card.

A failure at any step produces a safe outcome with no invented result.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.modules.assessments.calibration import TemperatureCalibration, softmax
from app.modules.assessments.decision import Decision, DecisionError, decide
from app.modules.assessments.explanation import NOT_A_DIAGNOSIS, Explanation, explain
from app.modules.assessments.inference import (
    InferenceAdapter,
    InferenceFailure,
    InferenceRequest,
    InferenceRunner,
    NullInferenceAdapter,
)
from app.modules.assessments.policy import TriagePolicy
from app.modules.assessments.quality import ImageMetrics, QualityOutcome, evaluate_quality
from app.modules.assessments.registry import ModelNotApproved, ModelRegistry
from app.modules.assessments.schemas import (
    AssessmentHistory,
    AssessmentRequest,
    AssessmentResponse,
    CandidateOut,
)
from app.modules.assessments.store import InMemoryPredictionStore, PredictionRecord

Clock = Callable[[], datetime]


class AssessmentFailure(Exception):
    """A typed, safe service failure."""

    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _abstained_decision(reason: str) -> Decision:
    return Decision(
        state="abstained",
        reason_code=reason,  # type: ignore[arg-type]
        candidates=(),
        confidence_band=None,
        top1_label=None,
        top1_score=None,
        margin=0.0,
        entropy=0.0,
        ood_score=0.0,
        calibrated=False,
    )


class AssessmentService:
    def __init__(
        self,
        *,
        policy: TriagePolicy,
        registry: ModelRegistry,
        store: InMemoryPredictionStore,
        adapter: InferenceAdapter | None = None,
        runner: InferenceRunner | None = None,
        calibration: TemperatureCalibration | None = None,
        clock: Clock | None = None,
        registry_base_dir: Path | None = None,
    ) -> None:
        self._policy = policy
        self._registry = registry
        self._store = store
        self._adapter = adapter if adapter is not None else NullInferenceAdapter()
        self._runner = runner if runner is not None else InferenceRunner()
        self._calibration = calibration
        self._clock = clock if clock is not None else _utcnow
        self._registry_base_dir = registry_base_dir

    # ------------------------------------------------------------------ API

    def assess(self, request: AssessmentRequest) -> AssessmentResponse:
        now = self._clock()
        existing = self._store.find_by_client(request.client_assessment_id)
        if existing is not None:
            return self._to_response(existing)

        model_version = request.model_version or self._policy.default_model_version

        if request.crop_id not in self._policy.supported_crops:
            return self._persist(
                request=request,
                now=now,
                model_version=model_version,
                state="unsupported_crop",
                abstain_reason="unsupported_crop",
                decision=_abstained_decision("unsupported_crop"),
                quality_result="not_run",
                quality_flags=(),
                quality_gate_version=self._policy.quality.version,
                calibrated=False,
                calibration_version=None,
                candidates=(),
                confidence_band=None,
                scores=None,
                ood_score=None,
                preprocessing_version=None,
                latency_ms=None,
                is_demo=self._policy.is_demo,
            )

        metrics = ImageMetrics(
            width=request.image.width,
            height=request.image.height,
            laplacian_variance=request.image.laplacian_variance,
            mean_luma=request.image.mean_luma,
            clipped_fraction=request.image.clipped_fraction,
            plant_presence=request.image.plant_presence,
        )
        quality = evaluate_quality(metrics, self._policy.quality)
        if not quality.passed:
            return self._persist(
                request=request,
                now=now,
                model_version=model_version,
                state="abstained",
                abstain_reason="quality_gate_failed",
                decision=_abstained_decision("quality_gate_failed"),
                quality_result=quality.result,
                quality_flags=quality.flags,
                quality_gate_version=quality.gate_version,
                calibrated=False,
                calibration_version=None,
                candidates=(),
                confidence_band=None,
                scores=None,
                ood_score=None,
                preprocessing_version=None,
                latency_ms=None,
                is_demo=self._policy.is_demo,
            )

        try:
            entry = self._registry.require_servable(
                model_version,
                taxonomy_version=self._policy.taxonomy_version,
                calibration_version=self._calibration.version if self._calibration else None,
                base_dir=self._registry_base_dir,
            )
            output, latency_ms = self._runner.run(
                self._adapter,
                InferenceRequest(
                    crop_id=request.crop_id,
                    content_hash=request.image.content_hash,
                    width=request.image.width,
                    height=request.image.height,
                ),
            )
            if output.model_version != entry.model_version:
                raise AssessmentFailure(
                    "model_version_mismatch",
                    "The model served a different version than the approved registry entry.",
                )
            if output.preprocessing_version != entry.preprocessing_version:
                raise AssessmentFailure(
                    "preprocessing_version_mismatch",
                    "The inference preprocessing does not match the approved model entry.",
                )
            if set(output.logits) != set(self._policy.labels):
                raise AssessmentFailure(
                    "label_map_mismatch",
                    "The model output does not match the configured class taxonomy.",
                )

            if entry.calibration_approved:
                if (
                    self._calibration is None
                    or self._calibration.version != entry.calibration_version
                ):
                    raise AssessmentFailure(
                        "calibration_unavailable",
                        "Calibration for this model is not available, so assessment is blocked.",
                    )
                probabilities = self._calibration.apply(
                    [float(output.logits[label]) for label in self._policy.labels]
                )
                calibrated = True
                calibration_version = self._calibration.version
            else:
                probabilities = softmax(
                    [float(output.logits[label]) for label in self._policy.labels]
                )
                calibrated = False
                calibration_version = None

            scores = dict(zip(self._policy.labels, probabilities, strict=True))
            decision = decide(
                scores,
                ood_score=output.ood_score,
                calibrated=calibrated,
                policy=self._policy,
            )
            candidates = tuple(
                CandidateOut(
                    label=candidate.label,
                    display_name=candidate.display_name,
                    rank=index + 1,
                    score=candidate.score if calibrated else None,
                )
                for index, candidate in enumerate(decision.candidates)
            )

            return self._persist(
                request=request,
                now=now,
                model_version=entry.model_version,
                state=decision.state,
                abstain_reason=decision.reason_code,
                decision=decision,
                quality_result=quality.result,
                quality_flags=quality.flags,
                quality_gate_version=quality.gate_version,
                calibrated=calibrated,
                calibration_version=calibration_version,
                candidates=candidates,
                confidence_band=decision.confidence_band,
                scores=scores,
                ood_score=decision.ood_score,
                preprocessing_version=entry.preprocessing_version,
                latency_ms=latency_ms,
                is_demo=self._policy.is_demo or entry.is_demo,
            )

        except ModelNotApproved as error:
            return self._failed(
                now=now,
                model_version=model_version,
                code=error.code,
                retryable=False,
            )
        except InferenceFailure as error:
            return self._failed(
                now=now,
                model_version=model_version,
                code=error.code,
                retryable=error.retryable,
            )
        except AssessmentFailure as error:
            return self._failed(
                now=now,
                model_version=model_version,
                code=error.code,
                retryable=error.retryable,
            )
        except DecisionError:
            return self._failed(
                now=now,
                model_version=model_version,
                code="decision_error",
                retryable=False,
            )

    def get(self, prediction_id: str) -> AssessmentResponse | None:
        record = self._store.get(prediction_id)
        return self._to_response(record) if record is not None else None

    def history(self, *, limit: int = 20, cursor: str | None = None) -> AssessmentHistory:
        records, next_cursor = self._store.list(limit=limit, cursor=cursor)
        return AssessmentHistory(
            items=[self._to_response(record) for record in records],
            next_cursor=next_cursor,
        )

    # ------------------------------------------------------------- internals

    def _decision_thresholds(self, *, calibrated: bool) -> dict:
        return {
            "score_kind": "calibrated_probability" if calibrated else "raw_score",
            "tau_c": {definition.label: definition.tau_c for definition in self._policy.classes},
            "margin": self._policy.decision.margin,
            "entropy": self._policy.decision.entropy,
            "ood_max": self._policy.decision.ood_max,
            "ood_enabled": self._policy.decision.ood_enabled,
        }

    def _persist(
        self,
        *,
        request: AssessmentRequest,
        now: datetime,
        model_version: str,
        state: str,
        abstain_reason: str | None,
        decision: Decision,
        quality_result: str,
        quality_flags: tuple[str, ...],
        quality_gate_version: str,
        calibrated: bool,
        calibration_version: str | None,
        candidates: tuple[CandidateOut, ...],
        confidence_band: str | None,
        scores: dict[str, float] | None,
        ood_score: float | None,
        preprocessing_version: str | None,
        latency_ms: float | None,
        is_demo: bool,
    ) -> AssessmentResponse:
        quality = QualityOutcome(
            result=quality_result,  # type: ignore[arg-type]
            flags=quality_flags,  # type: ignore[arg-type]
            gate_version=quality_gate_version,
            thresholds=self._policy.quality.model_dump(),
        )
        explanation: Explanation = explain(
            decision,
            self._policy,
            quality=quality if quality_result != "not_run" else None,
            supported_crops=self._policy.supported_crops,
        )

        record = PredictionRecord(
            prediction_id=f"pred_{uuid4().hex}",
            client_assessment_id=request.client_assessment_id,
            crop_id=request.crop_id,
            content_hash=request.image.content_hash,
            input_snapshot_ref=f"sha256:{request.image.content_hash}",
            state=state,
            abstained=state != "assessed",
            abstain_reason=abstain_reason,
            reason_text=explanation.text,
            next_steps=explanation.next_steps,
            not_a_diagnosis=True,
            quality_result=quality_result,
            quality_flags=quality_flags,
            quality_gate_version=quality_gate_version,
            candidates=candidates,
            confidence_band=confidence_band,
            calibrated=calibrated,
            calibration_version=calibration_version,
            model_version=model_version,
            taxonomy_version=self._policy.taxonomy_version,
            preprocessing_version=preprocessing_version,
            score_kind="calibrated_probability" if calibrated else "raw_score",
            scores=scores,
            decision_thresholds=self._decision_thresholds(calibrated=calibrated),
            ood_score=ood_score,
            latency_ms=latency_ms,
            generated_at=now,
            is_demo=is_demo,
        )
        self._store.append(record)
        return self._to_response(record)

    def _failed(
        self,
        *,
        now: datetime,
        model_version: str,
        code: str,
        retryable: bool,
    ) -> AssessmentResponse:
        if retryable:
            text = (
                "The photo assessment could not be completed right now. "
                f"{NOT_A_DIAGNOSIS} Retry, or request expert review if it keeps failing."
            )
            next_steps = ["retry", "request_review"]
        else:
            text = (
                "Photo assessment is not available for this image in this deployment. "
                f"{NOT_A_DIAGNOSIS} Request expert review if you need help."
            )
            next_steps = ["request_review"]
        return AssessmentResponse(
            assessment_id=None,
            state="failed",
            reason_code=code,
            reason_text=text,
            quality_flag=None,
            quality_flags=[],
            candidates=[],
            confidence_band=None,
            calibrated=False,
            calibration_version=None,
            model_version=model_version,
            taxonomy_version=self._policy.taxonomy_version,
            quality_gate_version=self._policy.quality.version,
            decision_thresholds=self._decision_thresholds(calibrated=False),
            ood_score=None,
            generated_at=now,
            is_demo=self._policy.is_demo,
            next_steps=next_steps,
            not_a_diagnosis=True,
            supported_crops=list(self._policy.supported_crops),
            error_code=code,
            retryable=retryable,
        )

    def _to_response(self, record: PredictionRecord) -> AssessmentResponse:
        return AssessmentResponse(
            assessment_id=record.prediction_id,
            state=record.state,  # type: ignore[arg-type]
            reason_code=record.abstain_reason,
            reason_text=record.reason_text,
            quality_flag=record.quality_flags[0] if record.quality_flags else None,
            quality_flags=list(record.quality_flags),
            candidates=list(record.candidates),
            confidence_band=record.confidence_band,
            calibrated=record.calibrated,
            calibration_version=record.calibration_version,
            model_version=record.model_version,
            taxonomy_version=record.taxonomy_version,
            quality_gate_version=record.quality_gate_version,
            decision_thresholds=record.decision_thresholds,
            ood_score=record.ood_score,
            generated_at=record.generated_at,
            is_demo=record.is_demo,
            next_steps=list(record.next_steps),
            not_a_diagnosis=record.not_a_diagnosis,
            supported_crops=list(self._policy.supported_crops),
            error_code=None,
            retryable=False,
        )

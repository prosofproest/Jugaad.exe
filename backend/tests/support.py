"""Shared synthetic fixtures for assessment tests.

Every artefact and policy here is explicitly synthetic and labelled as such.
No value in this file is a field result, a validated operating point or a
crop/target decision.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from app.modules.assessments.inference import InferenceOutput
from app.modules.assessments.policy import TriagePolicy, load_policy_file
from app.modules.assessments.registry import ModelRegistry
from app.modules.assessments.schemas import AssessmentRequest
from app.modules.assessments.service import AssessmentService
from app.modules.assessments.store import InMemoryPredictionStore

FIXTURES = Path(__file__).parent / "fixtures"
POLICY_PATH = FIXTURES / "synthetic_policy.json"
FIXED_TIME = datetime(2026, 11, 6, 6, 0, 0, tzinfo=timezone.utc)


def make_policy() -> TriagePolicy:
    return load_policy_file(POLICY_PATH)


def make_registry(
    tmp_path: Path,
    *,
    status: str = "approved",
    taxonomy_version: str = "synthetic-taxonomy-1",
    calibration_version: str | None = None,
    calibration_approved: bool = False,
    model_version: str = "synthetic-model-1",
    preprocessing_version: str = "prep-synthetic-1",
    artefact_bytes: bytes = b"synthetic test artefact, not a model\n",
    correct_checksum: bool = True,
) -> tuple[ModelRegistry, Path]:
    artefact = tmp_path / "model.synthetic.bin"
    artefact.write_bytes(artefact_bytes)
    digest = hashlib.sha256(artefact_bytes).hexdigest()
    if not correct_checksum:
        digest = "0" * 64

    entry = {
        "model_version": model_version,
        "status": status,
        "artefact_path": str(artefact.resolve()),
        "sha256": digest,
        "taxonomy_version": taxonomy_version,
        "preprocessing_version": preprocessing_version,
        "calibration_version": calibration_version,
        "calibration_approved": calibration_approved,
        "metrics": None,
        "metric_provenance": None,
        "is_demo": True,
        "created_at": "2026-11-06T00:00:00Z",
        "approved_at": "2026-11-06T00:00:00Z" if status == "approved" else None,
    }
    registry = ModelRegistry.model_validate({"schema_version": "1.0", "models": [entry]})
    return registry, artefact


class FakeAdapter:
    def __init__(
        self,
        *,
        logits: dict[str, float] | None = None,
        ood_score: float = 0.1,
        model_version: str = "synthetic-model-1",
        preprocessing_version: str = "prep-synthetic-1",
        error: Exception | None = None,
        delay_s: float = 0.0,
    ) -> None:
        self.logits = logits or {"lesion_like": 2.0, "healthy_like": 0.0, "other_like": -1.0}
        self.ood_score = ood_score
        self.model_version = model_version
        self.preprocessing_version = preprocessing_version
        self.error = error
        self.delay_s = delay_s
        self.calls: list = []

    def predict(self, request) -> InferenceOutput:
        self.calls.append(request)
        if self.delay_s:
            time.sleep(self.delay_s)
        if self.error is not None:
            raise self.error
        return InferenceOutput(
            logits=self.logits,
            ood_score=self.ood_score,
            model_version=self.model_version,
            preprocessing_version=self.preprocessing_version,
        )


def make_service(
    tmp_path: Path,
    *,
    adapter=None,
    calibration=None,
    registry: ModelRegistry | None = None,
    policy: TriagePolicy | None = None,
    timeout_s: float = 1.0,
    max_attempts: int = 1,
) -> tuple[AssessmentService, InMemoryPredictionStore]:
    from app.modules.assessments.inference import InferenceRunner

    policy = policy or make_policy()
    if registry is None:
        registry, _ = make_registry(
            tmp_path,
            calibration_approved=calibration is not None,
            calibration_version=calibration.version if calibration is not None else None,
        )
    store = InMemoryPredictionStore()
    service = AssessmentService(
        policy=policy,
        registry=registry,
        store=store,
        adapter=adapter or FakeAdapter(),
        runner=InferenceRunner(timeout_s=timeout_s, max_attempts=max_attempts),
        calibration=calibration,
        clock=lambda: FIXED_TIME,
    )
    return service, store


def make_request(
    *,
    client_assessment_id: str = "client-assessment-1",
    crop_id: str = "test_crop",
    content_hash: str = "a" * 64,
    model_version: str | None = None,
    width: int = 1200,
    height: int = 900,
    laplacian_variance: float = 250.0,
    mean_luma: float = 128.0,
    clipped_fraction: float = 0.01,
    plant_presence: float = 0.9,
) -> AssessmentRequest:
    return AssessmentRequest.model_validate(
        {
            "client_assessment_id": client_assessment_id,
            "crop_id": crop_id,
            "model_version": model_version,
            "image": {
                "filename": "synthetic.jpg",
                "content_type": "image/jpeg",
                "content_hash": content_hash,
                "width": width,
                "height": height,
                "laplacian_variance": laplacian_variance,
                "mean_luma": mean_luma,
                "clipped_fraction": clipped_fraction,
                "plant_presence": plant_presence,
            },
        }
    )


def write_registry_file(path: Path, registry: ModelRegistry) -> Path:
    path.write_text(
        json.dumps(registry.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    return path

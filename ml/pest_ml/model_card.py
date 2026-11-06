"""Render a model card that cannot be mistaken for a performance claim."""

from __future__ import annotations

from typing import Any

from .manifest import DatasetManifest
from .splits import SplitAssignment
from .train import TrainedModel


def render_model_card(
    model: TrainedModel,
    report: dict[str, Any],
    manifest: DatasetManifest,
    split: SplitAssignment,
) -> str:
    per_class_rows = "\n".join(
        "| {label} | {support} | {precision:.4f} | {recall:.4f} | {f1:.4f} |".format(
            label=label,
            support=values["support"],
            precision=values["precision"],
            recall=values["recall"],
            f1=values["f1"],
        )
        for label, values in report["per_class"].items()
    )
    split_rows = "\n".join(
        f"| {name} | {sum(counts[name] for counts in split.per_class.values())} |"
        for name in split.splits
    )
    warning = (
        "> **SYNTHETIC FIXTURE — NOT FOR FIELD USE.**\n"
        "> This card describes pipeline-verification output only. It is not a\n"
        "> trained image model, not a dataset result and not a performance claim.\n"
        "> Do not show its numbers to users, reviewers or funders as model quality."
    )
    return f"""# Model card — {model.model_version}

{warning}

## Intended use

- Verify that manifest -> grouped split -> training -> evaluation -> promotion
  plumbing works and is reproducible.
- Produce a checksummed artefact and a fail-closed registry entry in tests.

## Not intended for

- Photo assessment, triage, diagnosis or any user-facing decision.
- Field, pilot, clinical or regulatory claims.
- Replacing the missing crop/target taxonomy, dataset or operating point.

## Data

| Field | Value |
|---|---|
| Dataset id | `{manifest.dataset_id}` |
| Fixture kind | `{manifest.fixture_kind}` |
| Licence | `{manifest.licence}` |
| Provenance | `{manifest.provenance}` |
| Items | {len(manifest.items)} |
| Groups | {len(split.group_splits)} |
| Data fingerprint | `{manifest.data_fingerprint}` |
| Split fingerprint | `{split.fingerprint}` |

### Split sizes

| Split | Items |
|---|---|
{split_rows}

## Model

| Field | Value |
|---|---|
| Family | nearest-centroid fixture baseline |
| Version | `{model.model_version}` |
| Feature contract | `{model.feature_contract_version}` |
| Taxonomy | `{model.taxonomy_version}` |
| Artefact sha256 | `{model.checksum}` |
| Training data fingerprint | `{model.training_data_fingerprint}` |

## Evaluation (synthetic fixture only)

| Metric | Value |
|---|---|
| Macro F1 | {report["macro_f1"]:.6f} |
| Top-1 accuracy | {report["top_k_accuracy"]["1"]:.6f} |
| Abstention rate | {report["abstention_rate"]:.6f} |

### Per class

| Class | Support | Precision | Recall | F1 |
|---|---|---|---|---|
{per_class_rows}

Calibration: **not fitted and not approved**. Operating point: **not chosen**.

## Promotion status

`evaluated` only. The promotion gate refuses `approved` for a synthetic
fixture; approval additionally requires non-demo validation or field-test
evidence, an approved calibration artefact and human sign-off.

## Limitations

- Feature vectors are generated; no image feature extractor exists.
- No real dataset, licence review, consent record or subgroup analysis.
- Class list and taxonomy are synthetic; D1/D2 remain open.
- No calibrated confidence, threshold or coverage claim.
"""

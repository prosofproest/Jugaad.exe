"""End-to-end CLI for the reproducible synthetic ML scaffold.

Usage (from ``ml/``):

    ..\\backend\\.venv\\Scripts\\python -m pest_ml.pipeline

The run writes a checksummed artefact, split report, evaluation report, registry
entry and model card under ``ml/artifacts/``. It stops at ``evaluated``: the
promotion gate rejects ``approved`` for synthetic data.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .evaluate import evaluate_model
from .manifest import DatasetManifest, load_manifest
from .model_card import render_model_card
from .promote import build_registry_entry, registry_entry_json
from .splits import SplitAssignment, assign_splits
from .train import save_artefact, train_model

ML_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ML_ROOT / "fixtures" / "synthetic_manifest.json"
DEFAULT_OUT_DIR = ML_ROOT / "artifacts"
DEFAULT_MODEL_VERSION = "synthetic-centroid-0.1"
DEFAULT_SEED = "20261106"
DEFAULT_ARTEFACT_PATH = "artifacts/model.json"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="",
    )


def _items_for_split(manifest: DatasetManifest, split: SplitAssignment, name: str) -> list:
    selected = set(split.splits[name])
    return [item for item in manifest.items if item.image_id in selected]


def run_pipeline(
    manifest_path: str | Path,
    out_dir: str | Path,
    *,
    seed: str = DEFAULT_SEED,
    model_version: str = DEFAULT_MODEL_VERSION,
    trained_at: str | None = None,
    artefact_path: str = DEFAULT_ARTEFACT_PATH,
) -> dict[str, Any]:
    """Run the scaffold and return a JSON-safe summary."""

    manifest = load_manifest(manifest_path)
    split = assign_splits(manifest.items, seed=seed)
    train_items = _items_for_split(manifest, split, "train")
    test_items = _items_for_split(manifest, split, "test")

    model = train_model(
        train_items,
        manifest,
        model_version=model_version,
        trained_at=trained_at,
    )
    report = evaluate_model(
        model,
        test_items,
        manifest,
        split_name="test",
        evaluated_at=model.trained_at,
    )
    entry = build_registry_entry(model, report, artefact_path=artefact_path)

    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    save_artefact(model, destination / "model.json")
    _write_json(destination / "split_report.json", _split_report(split))
    _write_json(destination / "evaluation_report.json", report)
    _write_json(destination / "registry_entry.json", registry_entry_json(entry))
    (destination / "model_card.md").write_text(
        render_model_card(model, report, manifest, split),
        encoding="utf-8",
        newline="",
    )

    summary = {
        "schema_version": "1.0",
        "status": "evaluated",
        "is_demo": model.is_demo,
        "metric_provenance": model.metric_provenance,
        "dataset_id": manifest.dataset_id,
        "fixture_kind": manifest.fixture_kind,
        "model_version": model.model_version,
        "model_checksum": model.checksum,
        "split_fingerprint": split.fingerprint,
        "data_fingerprint": manifest.data_fingerprint,
        "artefact_path": artefact_path,
        "files": [
            "model.json",
            "split_report.json",
            "evaluation_report.json",
            "registry_entry.json",
            "model_card.md",
        ],
    }
    _write_json(destination / "pipeline_summary.json", summary)
    summary["output_dir"] = str(destination)
    return summary


def _split_report(split: SplitAssignment) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "seed": split.seed,
        "ratios": split.ratios,
        "fingerprint": split.fingerprint,
        "splits": {name: list(ids) for name, ids in split.splits.items()},
        "per_class": split.per_class,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="dataset manifest (default: committed synthetic fixture)",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT_DIR),
        help="output directory (default: ml/artifacts)",
    )
    parser.add_argument("--seed", default=DEFAULT_SEED, help="split seed")
    parser.add_argument(
        "--model-version", default=DEFAULT_MODEL_VERSION, help="artefact version label"
    )
    parser.add_argument(
        "--trained-at",
        default=None,
        help="ISO-8601 timestamp (default: manifest created_at, for reproducibility)",
    )
    parser.add_argument(
        "--artefact-path",
        default=DEFAULT_ARTEFACT_PATH,
        help="logical artefact path recorded in the registry entry",
    )
    args = parser.parse_args(argv)

    summary = run_pipeline(
        args.manifest,
        args.out,
        seed=args.seed,
        model_version=args.model_version,
        trained_at=args.trained_at,
        artefact_path=args.artefact_path,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

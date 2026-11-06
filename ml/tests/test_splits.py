from __future__ import annotations

import pytest
from pest_ml.manifest import DatasetItem, load_manifest
from pest_ml.splits import SplitError, assign_splits


def test_groups_never_cross_splits(manifest_path) -> None:
    manifest = load_manifest(manifest_path)
    split = assign_splits(manifest.items)

    image_split = {image_id: name for name, ids in split.splits.items() for image_id in ids}
    for item in manifest.items:
        assert image_split[item.image_id] == split.group_splits[item.group_id]

    all_ids = [image_id for ids in split.splits.values() for image_id in ids]
    assert sorted(all_ids) == sorted(item.image_id for item in manifest.items)
    assert len(set(all_ids)) == len(all_ids)

    for counts in split.per_class.values():
        assert all(counts[name] > 0 for name in ("train", "val", "test"))


def test_same_seed_is_deterministic(manifest_path) -> None:
    manifest = load_manifest(manifest_path)
    first = assign_splits(manifest.items, seed="fixed-seed")
    second = assign_splits(manifest.items, seed="fixed-seed")
    assert first.group_splits == second.group_splits
    assert first.fingerprint == second.fingerprint


def test_different_seed_changes_assignment(manifest_path) -> None:
    manifest = load_manifest(manifest_path)
    first = assign_splits(manifest.items, seed="seed-a")
    second = assign_splits(manifest.items, seed="seed-b")
    assert first.group_splits != second.group_splits
    assert first.fingerprint != second.fingerprint


def test_rejects_invalid_ratios(manifest_path) -> None:
    manifest = load_manifest(manifest_path)
    with pytest.raises(SplitError, match="sum to 1"):
        assign_splits(manifest.items, ratios={"train": 0.5, "val": 0.5, "test": 0.5})


def test_rejects_too_few_groups_per_class() -> None:
    items = [
        DatasetItem(
            image_id=f"{label}-{group}",
            group_id=f"{label}-{group}",
            label=label,
            features=(0.0, 0.0, 0.0, 0.0),
            is_demo=True,
            synthetic=True,
        )
        for label in ("a", "b")
        for group in range(2)
    ]
    with pytest.raises(SplitError, match="at least 3 groups"):
        assign_splits(items)

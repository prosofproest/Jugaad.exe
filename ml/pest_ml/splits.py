"""Grouped, stratified, deterministic dataset splits.

Splits are assigned by ``group_id`` (for example a plant, farm or capture
session), never by image. A group therefore appears in exactly one split, which
prevents the image-level leakage the project forbids. Assignment is
content-addressed by ``seed`` so the same inputs always produce the same split.

The scaffold requires ``train``/``val``/``test`` and at least as many groups per
class as there are splits. It fails closed rather than silently leaving a class
out of evaluation.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .manifest import DatasetItem, canonical_json_bytes

DEFAULT_RATIOS = {"train": 0.6, "val": 0.2, "test": 0.2}
REQUIRED_SPLITS = ("train", "val", "test")


class SplitError(ValueError):
    """Raised when splits cannot be produced without leakage or gaps."""


@dataclass(frozen=True)
class SplitAssignment:
    splits: dict[str, tuple[str, ...]]
    group_splits: dict[str, str]
    per_class: dict[str, dict[str, int]]
    fingerprint: str
    ratios: dict[str, float]
    seed: str


def _validate_ratios(ratios: Mapping[str, float]) -> dict[str, float]:
    if set(ratios) != set(REQUIRED_SPLITS):
        raise SplitError(f"ratios must define exactly {REQUIRED_SPLITS}")
    normalized: dict[str, float] = {}
    for name in REQUIRED_SPLITS:
        value = ratios[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SplitError(f"ratio '{name}' must be a number")
        number = float(value)
        if not math.isfinite(number) or number <= 0:
            raise SplitError(f"ratio '{name}' must be finite and positive")
        normalized[name] = number
    total = sum(normalized.values())
    if abs(total - 1.0) > 1e-9:
        raise SplitError("ratios must sum to 1")
    return normalized


def _rank(seed: str, label: str, group_id: str) -> str:
    return hashlib.sha256(f"{seed}:{label}:{group_id}".encode()).hexdigest()


def _quotas(n_groups: int, ratios: Mapping[str, float]) -> dict[str, int]:
    """Largest-remainder quotas with a one-per-split floor when possible."""

    names = list(REQUIRED_SPLITS)
    if n_groups < len(names):
        raise SplitError(
            f"a class needs at least {len(names)} groups for grouped splits, found {n_groups}"
        )

    raw = {name: ratios[name] * n_groups for name in names}
    quota = {name: math.floor(raw[name]) for name in names}
    remainder = n_groups - sum(quota.values())
    order = sorted(names, key=lambda name: (-(raw[name] - quota[name]), names.index(name)))
    for name in order[:remainder]:
        quota[name] += 1

    if any(value == 0 for value in quota.values()):
        quota = {name: 1 for name in names}
        remaining = n_groups - len(names)
        raw_remaining = {name: ratios[name] * remaining for name in names}
        add = {name: math.floor(raw_remaining[name]) for name in names}
        leftover = remaining - sum(add.values())
        order = sorted(
            names,
            key=lambda name: (
                -(raw_remaining[name] - add[name]),
                names.index(name),
            ),
        )
        for name in order[:leftover]:
            add[name] += 1
        for name in names:
            quota[name] += add[name]
    return quota


def assign_splits(
    items: Sequence[DatasetItem],
    *,
    ratios: Mapping[str, float] | None = None,
    seed: str = "20261106",
) -> SplitAssignment:
    """Assign every item to one split without separating a group."""

    if not items:
        raise SplitError("at least one dataset item is required")
    if not seed:
        raise SplitError("seed must be a non-empty string")
    normalized = _validate_ratios(ratios or DEFAULT_RATIOS)

    groups: dict[str, list[DatasetItem]] = {}
    group_label: dict[str, str] = {}
    for item in items:
        groups.setdefault(item.group_id, []).append(item)
        previous = group_label.setdefault(item.group_id, item.label)
        if previous != item.label:
            raise SplitError(f"group '{item.group_id}' spans multiple labels")

    classes = sorted({item.label for item in items})
    group_splits: dict[str, str] = {}
    per_class: dict[str, dict[str, int]] = {
        label: {name: 0 for name in REQUIRED_SPLITS} for label in classes
    }

    for label in classes:
        label_groups = sorted(
            (
                group_id
                for group_id, group_label_value in group_label.items()
                if group_label_value == label
            ),
            key=lambda group_id: _rank(seed, label, group_id),
        )
        quota = _quotas(len(label_groups), normalized)
        cursor = 0
        for name in REQUIRED_SPLITS:
            count = quota[name]
            for group_id in label_groups[cursor : cursor + count]:
                group_splits[group_id] = name
            per_class[label][name] = count
            cursor += count

    splits: dict[str, list[str]] = {name: [] for name in REQUIRED_SPLITS}
    for item in items:
        splits[group_splits[item.group_id]].append(item.image_id)

    assigned = [image_id for name in REQUIRED_SPLITS for image_id in splits[name]]
    if sorted(assigned) != sorted(item.image_id for item in items):
        raise SplitError("split assignment is not a partition of the dataset")

    fingerprint = hashlib.sha256(
        canonical_json_bytes(
            {
                "seed": seed,
                "ratios": normalized,
                "group_splits": group_splits,
            }
        )
    ).hexdigest()

    return SplitAssignment(
        splits={name: tuple(sorted(ids)) for name, ids in splits.items()},
        group_splits=group_splits,
        per_class=per_class,
        fingerprint=fingerprint,
        ratios=normalized,
        seed=seed,
    )

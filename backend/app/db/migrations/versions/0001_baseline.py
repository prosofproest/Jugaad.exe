"""Baseline: empty schema.

Revision ID: 0001_baseline
Revises: None
Create Date: 2026-11-06

The baseline exists so every later migration has a parent and CI can prove
that a database creates from zero. Feature tables (identity, observations,
media, reviews, audit) land as separate, additive revisions in Phase 2.
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

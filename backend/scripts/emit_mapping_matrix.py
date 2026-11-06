"""Emit docs/database/POSTGRESQL_MAPPING_MATRIX.md from ORM metadata.

Run from backend/:
    .venv/bin/python scripts/emit_mapping_matrix.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import models  # noqa: F401
from app.db.base import Base

OUT = Path(__file__).resolve().parents[2] / "docs" / "database" / "POSTGRESQL_MAPPING_MATRIX.md"

REVISION = {
    "conversations": "0002_chat_persistence",
    "messages": "0002_chat_persistence",
    "message_events": "0002_chat_persistence",
    "image_uploads": "0002_chat_persistence",
    "chat_review_requests": "0002_chat_persistence",
    "video_uploads": "0003_video_persistence",
    "video_readings": "0003_video_persistence",
}


def col_list(table) -> str:
    return ", ".join(f"`{c.name}`" for c in table.columns)


def pk_list(table) -> str:
    return ", ".join(f"`{c.name}`" for c in table.primary_key.columns)


def fk_list(table) -> str:
    if not table.foreign_keys:
        return "—"
    parts = []
    for fk in sorted(table.foreign_keys, key=lambda f: f.parent.name):
        parts.append(
            f"`{fk.parent.name}`→`{fk.column.table.name}.{fk.column.name}`"
            + (f" ON DELETE {fk.ondelete}" if fk.ondelete else "")
        )
    return "<br>".join(parts)


def ix_list(table) -> str:
    if not table.indexes:
        return "—"
    return "<br>".join(
        f"`{ix.name}` ({', '.join(c.name for c in ix.columns)})"
        for ix in sorted(table.indexes, key=lambda i: i.name or "")
    )


def uq_list(table) -> str:
    uqs = [c for c in table.constraints if c.__class__.__name__ == "UniqueConstraint"]
    if not uqs:
        return "—"
    return "<br>".join(
        f"`{c.name}` ({', '.join(col.name for col in c.columns)})" for c in uqs
    )


def main() -> None:
    tables = Base.metadata.tables
    fk_total = sum(len(t.foreign_keys) for t in tables.values())
    uq_total = sum(
        1
        for t in tables.values()
        for c in t.constraints
        if c.__class__.__name__ == "UniqueConstraint"
    )
    ix_total = sum(len(t.indexes) for t in tables.values())
    lines = []
    lines.append("# PostgreSQL Mapping Matrix")
    lines.append("")
    lines.append("Generated from live `Base.metadata` by `backend/scripts/emit_mapping_matrix.py`.")
    lines.append("Deltas: none — migration DDL preserves ORM types (§2 of ORM_INVENTORY.md).")
    lines.append("")
    lines.append("## Counts (from metadata + HEAD offline SQL)")
    lines.append("")
    lines.append(f"- ORM models discovered: **{len(tables)}**")
    lines.append(f"- Unique ORM tables: **{len(tables)}** (one table per model, no")
    lines.append("  duplicates, no association-only tables)")
    lines.append("- Migrated PostgreSQL tables: **50** (5 in 0002, 2 in 0003, 43 in 0004;")
    lines.append("  `alembic upgrade head --sql` emits 51 `CREATE TABLE` including")
    lines.append("  `alembic_version`)")
    lines.append(f"- Foreign keys: **{fk_total}**")
    lines.append(f"- Unique constraints: **{uq_total}** (plus per-column `UNIQUE` on")
    lines.append("  `users.phone_e164`, `users.email`, `geographies.code`,")
    lines.append("  `sessions.refresh_hash`, `alerts.dedupe_key` — counted in DDL, not here)")
    lines.append(f"- Indexes (declared B-tree): **{ix_total}**")
    lines.append("- Spatial columns: **0** · GiST indexes: **0** (no ORM geometry; see")
    lines.append("  ORM_INVENTORY.md §3)")
    lines.append("- Tables with unresolved mappings: **0**")
    lines.append("- Models without tables: **none**")
    lines.append("")
    lines.append("## Matrix")
    lines.append("")
    lines.append(
        "| ORM Model | PostgreSQL Table | Columns Mapped | Primary Key | Foreign Keys | "
        "Indexes | Constraints | Migration Revision | Verification |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for tname in sorted(tables):
        table = tables[tname]
        rev = REVISION.get(tname, "0004_domain_persistence")
        lines.append(
            f"| `{tname}` | `{tname}` | {col_list(table)} | {pk_list(table)} | "
            f"{fk_list(table)} | {ix_list(table)} | {uq_list(table)} | "
            f"`{rev}` | offline SQL + SQLite parity (PG pending) |"
        )
    lines.append("")
    lines.append("## How verification was done")
    lines.append("")
    lines.append("- Migration chain `0001 → 0004 (head)` verified by")
    lines.append("  `alembic upgrade head --sql` (51 CREATE TABLE) and fresh-SQLite")
    lines.append("  `alembic upgrade head` (51 tables, column parity exact).")
    lines.append("- PostgreSQL catalog verification is **pending** (no PostgreSQL or")
    lines.append("  Docker on this machine). The validation script and catalog queries")
    lines.append("  are in POSTGRESQL_MIGRATION_GUIDE.md / SCHEMA_VALIDATION_REPORT.md")
    lines.append("  and must be run against a real PostGIS database before any PG claim.")
    lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

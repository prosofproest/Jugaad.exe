"""Generate 0004_domain_persistence from ORM metadata (offline, dialect-neutral).

Usage (from backend/):
    .venv/bin/python scripts/generate_domain_migration.py

Writes backend/app/db/migrations/versions/0004_domain_persistence.py
covering the 43 tables not yet migrated (50 total minus 5 chat + 2 video).
Table creation order comes from SQLAlchemy's topological sort so every FK
references an earlier table. PostGIS extension is enabled as the first
statement (the backend ORM has zero geometry columns; see models.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

BACKEND = Path(__file__).resolve().parents[1]
OUT = BACKEND / "app" / "db" / "migrations" / "versions" / "0004_domain_persistence.py"

ALREADY = {
    "conversations",
    "messages",
    "message_events",
    "image_uploads",
    "chat_review_requests",
    "video_uploads",
    "video_readings",
}


def col_expr(column) -> str:
    """Render a column preserving its actual SQLAlchemy type.

    No type is silently widened: JSON stays JSON, String lengths are kept,
    Numeric precision/scale are kept. The only dialect nuance is timestamps:
    ``UTCDateTime`` (impl ``DateTime`` without timezone) stores naive UTC and
    renders as ``TIMESTAMP WITHOUT TIME ZONE`` on PostgreSQL, while explicit
    ``DateTime(timezone=True)`` (chat/video ORMs) renders as ``TIMESTAMPTZ``.
    Emitting ``timezone=True`` for both would silently convert every backend
    timestamp — a data-semantics change, not a cosmetic one.
    """
    t = column.type
    tname = t.__class__.__name__
    if tname == "String":
        base = f'sa.String(length={t.length})' if t.length else "sa.String()"
    elif tname == "Text":
        base = "sa.Text()"
    elif tname == "Integer":
        base = "sa.Integer()"
    elif tname == "Float":
        base = "sa.Float()"
    elif tname == "Boolean":
        base = "sa.Boolean()"
    elif tname == "Numeric":
        base = f"sa.Numeric(precision={t.precision}, scale={t.scale})"
    elif tname == "JSON":
        base = "sa.JSON()"
    elif tname == "UTCDateTime":
        # TypeDecorator over DateTime (naive, no timezone) → TIMESTAMP
        # WITHOUT TIME ZONE on PostgreSQL. Must NOT use timezone=True.
        base = "sa.DateTime()"
    elif tname == "DateTime":
        base = "sa.DateTime(timezone=True)" if t.timezone else "sa.DateTime()"
    else:
        base = f"sa.{tname}()"
    parts = [base]
    if column.server_default is not None:
        parts.append("server_default=sa.func.now()")
    parts.append("nullable=%s" % ("False" if not column.nullable else "True"))
    return f"sa.Column({column.name!r}, {', '.join(parts)})"


def main() -> None:
    from app.db import models  # noqa: F401  (registers every table)
    from app.db.base import Base

    ordered = [t for t in Base.metadata.sorted_tables if t.name not in ALREADY]
    assert len(ordered) == 43, len(ordered)

    lines = []
    lines.append('"""Identity, domain, forecast, advisory, review and registry persistence.')
    lines.append("")
    lines.append("Revision ID: 0004_domain_persistence")
    lines.append("Revises: 0003_video_persistence")
    lines.append("Create Date: 2026-11-06")
    lines.append("")
    lines.append("Additive only. Creates the 43 tables not covered by 0002/0003 plus")
    lines.append("the PostGIS extension. Tables are created in dependency order so every")
    lines.append("foreign key references an earlier table. Downgrade drops the tables in")
    lines.append("reverse dependency order and then drops the extension; the chat/video")
    lines.append("tables from 0002/0003 are untouched. The extension DROP fails if any")
    lines.append("non-ORM object depends on it — see MIGRATION_RECOVERY_GUIDE.md.")
    lines.append("")
    lines.append("PostGIS note: the backend ORM declares no geometry columns (the pilot")
    lines.append("API only serves block/mandal aggregates; geometry arrives when boundary")
    lines.append("data is approved). The extension is still enabled so spatial columns")
    lines.append("and GiST indexes can be added without a new extension migration. The")
    lines.append("reference schema (``database/schema/01-schema.sql``) geometry is a")
    lines.append("documented drift — it is not recreated here (see ORM_INVENTORY.md).")
    lines.append('"""')
    lines.append("")
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from collections.abc import Sequence")
    lines.append("")
    lines.append("import sqlalchemy as sa")
    lines.append("from alembic import op")
    lines.append("")
    lines.append('revision: str = "0004_domain_persistence"')
    lines.append('down_revision: str | None = "0003_video_persistence"')
    lines.append("branch_labels: str | Sequence[str] | None = None")
    lines.append("depends_on: str | Sequence[str] | None = None")
    lines.append("")
    lines.append("")
    lines.append("def _is_postgresql() -> bool:")
    lines.append('    """True only on PostgreSQL (SQLite dev/tests have no extensions)."""')
    lines.append("")
    lines.append('    return op.get_bind().dialect.name == "postgresql"')
    lines.append("")
    lines.append("")
    lines.append("def _enable_postgis() -> None:")
    lines.append('    """Enable PostGIS on PostgreSQL, warning when unavailable.')
    lines.append("")
    lines.append("    The ORM declares zero geometry columns, so the extension is inert")
    lines.append("    for this schema and a missing extension must not block table")
    lines.append("    creation. Production PostgreSQL MUST provide postgis (compose")
    lines.append("    uses postgis/postgis:16-3.4); an isolated test database without it")
    lines.append("    logs a warning and continues. PostGIS verification is then")
    lines.append("    reported as blocked, never passed.")
    lines.append("")
    lines.append("    The CREATE runs in a SAVEPOINT: a failed extension (missing control")
    lines.append("    file) rolls back to the savepoint without aborting the migration")
    lines.append("    transaction, so the 43 CREATE TABLEs that follow still execute.")
    lines.append('    """')
    lines.append("")
    lines.append("    if not _is_postgresql():")
    lines.append("        return")
    lines.append("    bind = op.get_bind()")
    lines.append("    try:")
    lines.append("        from alembic import context as _ctx")
    lines.append("")
    lines.append("        _offline = _ctx.is_offline_mode()")
    lines.append("    except Exception:  # noqa: BLE001")
    lines.append("        _offline = False")
    lines.append("    if _offline:")
    lines.append("        # Buffered DDL only; never executes, so no abort is possible.")
    lines.append('        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")')
    lines.append("        return")
    lines.append("    try:")
    lines.append("        with bind.begin_nested():")
    lines.append('            bind.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS postgis")')
    lines.append("    except Exception as exc:  # noqa: BLE001 - inert schema, warn only")
    lines.append('        print(f"[0004] WARNING: postgis unavailable ({exc}); continuing without it.")')
    lines.append("")
    lines.append("")
    lines.append("def upgrade() -> None:")
    lines.append("    _enable_postgis()")

    for table in ordered:
        lines.append("")
        # columns
        cols = [col_expr(c) for c in table.columns]
        # primary key constraint (named via NAMING_CONVENTION)
        pk_cols = [c.name for c in table.primary_key.columns]
        pk_name = f"pk_{table.name}"
        # foreign keys
        fks = []
        for fk in table.foreign_keys:
            local = fk.parent.name
            remote = f"{fk.column.table.name}.{fk.column.name}"
            fk_name = f"fk_{table.name}_{local}_{fk.column.table.name}"
            ondel = f', ondelete="{fk.ondelete}"' if fk.ondelete else ""
            fks.append(
                f'        sa.ForeignKeyConstraint(["{local}"], ["{remote}"], name="{fk_name}"{ondel}),'
            )
        # unique constraints
        for con in table.constraints:
            if con.__class__.__name__ == "UniqueConstraint":
                cols_names = ", ".join(f'"{c.name}"' for c in con.columns)
                uq_name = con.name or f"uq_{table.name}_{'_'.join(c.name for c in con.columns)}"
                fks.append(f'        sa.UniqueConstraint({cols_names}, name="{uq_name}"),')
        lines.append(f"    op.create_table(")
        lines.append(f'        "{table.name}",')
        for c in cols:
            lines.append(f"        {c},")
        for f in fks:
            lines.append(f)
        lines.append(f'        sa.PrimaryKeyConstraint({", ".join(f"{c!r}" for c in pk_cols)}, name="{pk_name}"),')
        lines.append("    )")
        for ix in sorted(table.indexes, key=lambda i: i.name or ""):
            ix_name = ix.name or f"ix_{table.name}_{'_'.join(c.name for c in ix.columns)}"
            col_names = ", ".join(f'"{c.name}"' for c in ix.columns)
            lines.append(
                f'    op.create_index("{ix_name}", "{table.name}", [{col_names}])'
            )

    lines.append("")
    lines.append("")
    lines.append("def downgrade() -> None:")
    for table in reversed(ordered):
        for ix in sorted(table.indexes, key=lambda i: i.name or "", reverse=True):
            ix_name = ix.name or f"ix_{table.name}_{'_'.join(c.name for c in ix.columns)}"
            lines.append(f'    op.drop_index("{ix_name}", table_name="{table.name}")')
        # Drop indexes explicitly (0002/0003 style), then the table. Unique
        # constraints die with the table; SQLite cannot ALTER constraints, so
        # no drop_constraint is emitted (see MIGRATION_RECOVERY_GUIDE.md).
        lines.append(f'    op.drop_table("{table.name}")')
    lines.append("")
    lines.append("    # NOTE: DROP EXTENSION fails if any non-ORM object (reference schema,")
    lines.append("    # manual geometry) depends on PostGIS. On failure, keep the extension:")
    lines.append("    # it is inert on a schema with no spatial columns.")
    lines.append("    if _is_postgresql():")
    lines.append("        try:")
    lines.append('            op.execute("DROP EXTENSION IF EXISTS postgis")')
    lines.append("        except Exception as exc:  # noqa: BLE001 - keep inert extension")
    lines.append('            print(f"[0004] WARNING: postgis drop skipped ({exc})")')
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT} ({len(ordered)} tables)")


if __name__ == "__main__":
    main()

# PostgreSQL Migration Guide

## 1. Authority

Backend Alembic (`backend/app/db/migrations`, `env.py` loading `app.db.models`)
is the **single operational migration system** (ADR-002). `database/alembic/`
and `database/schema/*.sql` are **reference only** — never apply them to a
deployment by hand. `Base.metadata.create_all()` is for local dev/tests only
(`app/db/session.py::init_db`); production must use Alembic.

## 2. Requirements

- PostgreSQL 16 + PostGIS 3.x (compose: `postgis/postgis:16-3.4`)
- Backend env: `APP_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db`
  (never commit a real URL). Local default is SQLite; compose injects Postgres.

## 3. Fresh installation

```bash
cd backend
.venv/bin/python -m pip install -r requirements.txt  # or uv pip install
APP_DATABASE_URL=postgresql+psycopg://ps03:ps03@localhost:5432/ps03 \
  .venv/bin/python -m alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Chain: `0001_baseline → 0002_chat_persistence → 0003_video_persistence →
0004_domain_persistence (head)`. `0004` creates the remaining 43 tables and
runs `CREATE EXTENSION IF NOT EXISTS postgis` (PostgreSQL only; skipped on
SQLite).

## 4. Existing database adoption

Do **not** `upgrade head` blindly. Inspect first:

```bash
.venv/bin/python -m alembic current
.venv/bin/python -m alembic history
# Compare catalogs: psql $APP_DATABASE_URL -c "\dt" and
# SELECT table_name FROM information_schema.tables WHERE table_schema='public'
```

- If `alembic_version` is at `0003` (or earlier): `alembic upgrade head`
  applies `0004` additively. No data is touched.
- If no `alembic_version` but tables exist (e.g. created by `init_db`):
  do **not** stamp blindly. Run the drift check (§5); stamp only when every
  expected table/column matches, otherwise backfill the missing objects
  manually. Never drop or recreate user data for adoption.

## 5. Upgrade / drift detection

Daily / CI:

```bash
# Offline review (no DB needed)
.venv/bin/python -m alembic upgrade head --sql > /tmp/migrations.sql

# Live drift vs SQLite dev DB (tables + columns)
.venv/bin/python scripts/check_schema_drift.py

# Live drift vs PostgreSQL (tables, columns, FKs, indexes — full catalog)
APP_DATABASE_URL=postgresql+psycopg://... .venv/bin/python scripts/check_schema_drift.py --postgres
.venv/bin/python -m alembic check  # reports ORM-vs-DB differences (Alembic ≥1.13)
```

`scripts/check_schema_drift.py` compares `Base.metadata` against the live
database table-by-table (missing/extra tables and columns, nullability,
PK/FK/unique/index sets; on PostgreSQL also column `data_type` for the
naive vs tz-aware timestamp distinction and `now()` server defaults) and
exits non-zero on any mismatch. Missing PostGIS is a WARNING (the ORM has
zero geometry columns), never a silent pass.

## 6. Downgrade limitations

- `0004` downgrade drops its 43 tables in reverse dependency order and then
  `DROP EXTENSION IF EXISTS postgis`. If any non-ORM object depends on PostGIS
  (reference schema, manual geometry), the DROP fails — keep the extension;
  it is inert with no spatial columns.
- Downgrade is for disposable test databases only. Production is forward-only.
  Practice the recovery guide before touching a real database.

## 7. Adding a model safely

1. Add the `Mapped` model to `app/db/models.py` (or chat/video ORM) with
   explicit types/nullability. No `TEXT`/`JSONB` upgrade without review.
2. Regenerate docs: `python scripts/emit_orm_inventory.py` and
   `python scripts/emit_mapping_matrix.py`; review the diffs.
3. Generate a revision: `python -m alembic revision -m "add <model>" --autogenerate`
   against a scratch DB, **review every operation**, add indexes/server
   defaults by hand, give the downgrade a rollback note.
4. Test: `pytest tests/test_migrations.py` + drift check (§5), then upgrade a
   scratch PostgreSQL database before merging.

## 8. Troubleshooting

See MIGRATION_RECOVERY_GUIDE.md. Common causes: SQLite/Postgres URL mixups
(`APP_DATABASE_URL` semantics), `extension` syntax error on SQLite (now
gated), missing `alembic_version` adoptions, and FK order issues solved by
`sorted_tables` ordering.

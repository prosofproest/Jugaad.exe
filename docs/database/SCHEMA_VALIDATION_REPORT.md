# Schema Validation Report

Date: 2026-11-06. Machine: macOS. PostgreSQL via embedded `pgserver` 0.1.4
(PostgreSQL **16.2** on aarch64, Unix socket, `/T/opencode/pgtest`).

## Verified (executed)

| Check | Command / scope | Result |
|---|---|---|
| Offline migration SQL | `alembic upgrade head --sql` | **PASS** — 51 `CREATE TABLE` (50 app + `alembic_version`), `0001→0004 (head)` |
| Fresh-SQLite Alembic apply | `APP_DATABASE_URL=sqlite:///<tmp> alembic upgrade head` | **PASS** — 51 tables; tables/columns match metadata exactly |
| Fresh-PostgreSQL Alembic apply | `APP_DATABASE_URL=postgresql+psycopg://… alembic upgrade head` (pgserver 16.2) | **PASS** — `UPGRADE OK`, `alembic_version=0004_domain_persistence`, 0004 warns `postgis unavailable` and continues (savepoint-isolated) |
| PostgreSQL catalog counts | `information_schema` + `pg_indexes` | tables **51**, FK constraints **51**, UNIQUE constraints **13**, indexes **119** |
| Timestamp types (catalog) | `information_schema.columns.data_type` | `users.created_at`=**timestamp without time zone** (UTCDateTime naive), `conversations.created_at`=**timestamp with time zone**, `video_uploads.created_at`=**with tz** |
| SQLAlchemy on PostgreSQL | insert/query/update/delete via `Session` | **PASS** — Crop/Geography/Role/User insert + count + delete |
| Drift detector (SQLite) | `scripts/check_schema_drift.py` | **PASS** — 50 tables, columns/FK/UQ/index match |
| Drift detector (PostgreSQL) | `check(..., postgres=True)` | **PASS** — same parity incl. per-column types + `now()` defaults; PostGIS printed as WARNING/BLOCKED (see below) |
| Downgrade → re-upgrade | PG: `downgrade base → upgrade head`; SQLite: same | **PASS** — 51→1→51 tables on both |
| Migration tests (PG) | `pytest tests/test_migrations.py` with `APP_DATABASE_URL=postgresql…` | **6 passed, 1 skipped** (PostGIS spatial skipped) |
| Migration tests (SQLite) | same without PG URL | **3 passed, 4 skipped** |
| Backend suite | `pytest` | **359 passed, 4 skipped** |
| Database tests | `pytest database/tests` | **70 passed** |
| Ruff | `check` + `format --check` | clean (139 files) |
| `alembic check` | SQLite HEAD | *No new upgrade operations detected* |

## Skipped (honestly reported, not passed)

- PostGIS extension + spatial columns/GiST: **SKIPPED/BLOCKED** — pgserver bundle
  ships no PostGIS control file (`extension "postgis" is not available`), so
  `test_postgresql_postgis_extension_and_spatial` skips. The backend ORM has
  **zero geometry columns** by design; production must provide PostGIS
  (compose `postgis/postgis:16-3.4`). No spatial test is claimed as passed.

## UTCDateTime correction (this audit)

The generator previously emitted `sa.DateTime(timezone=True)` for every
timestamp, producing `TIMESTAMPTZ` for backend `UTCDateTime` columns whose
ORM DDL is `TIMESTAMP WITHOUT TIME ZONE` (verified via `CreateTable` +
catalog). Fixed: `UTCDateTime → sa.DateTime()` (no tz), explicit
`DateTime(timezone=True)` stays `TIMESTAMPTZ`. `0004` was regenerated; no
unsafe data conversion was performed (fresh DBs only — an existing database
with mixed semantics needs a data migration, documented as open decision).

## Known drifts (documented, not hidden)

1. Reference `database/schema/01-schema.sql` (UUID PKs, `timestamptz`,
   `jsonb`, CHECKs, 3 geometry cols, 13 append-only triggers) vs backend ORM
   (`VARCHAR(64)` ids, mixed timestamp semantics, `JSON`, zero checks, zero
   geometry, service-enforced append-only). Backend is authority.
2. Mixed timestamp semantics (naive UTC vs TIMESTAMPTZ) preserved as-is.
3. `database/alembic` (0001/0002 reference history) must never be applied to
   the same database (see MIGRATION_GUIDE §1).

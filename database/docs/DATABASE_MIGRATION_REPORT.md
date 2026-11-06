# CropSentinel AI — Database Migration Architecture Report

**Migration Framework:** Alembic 1.20.1
**Authority:** CropSentinel AI Schema Architecture
**Target Dialect:** PostgreSQL 16+ with PostGIS 3.x and pgvector

---

## 1. Migration History & Revision DAG

```
None
  └── 0001_initial_schema (Phase 1 Baseline Slice: 40 tables)
        └── 0002_cropsentinel_master_schema (Master Architecture: 11 Domains, 76 Tables)
```

| Revision ID | Description | Down Revision | Path | Status |
|---|---|---|---|---|
| `0001_initial_schema` | Phase 1 schema slice baseline | `None` | `database/alembic/versions/0001_initial_schema.py` | APPLIED |
| `0002_cropsentinel_master_schema` | Complete master database across 11 domains | `0001_initial_schema` | `database/alembic/versions/0002_cropsentinel_master_schema.py` | READY |

---

## 2. Upgrade & Downgrade Safety
- **Additive & Safe:** Migration `0002` adds all remaining domain tables using `CREATE TABLE IF NOT EXISTS`.
- **PostGIS Extension Guard:** Checks `CREATE EXTENSION IF NOT EXISTS postgis` and `pgcrypto` before table creation.
- **pgvector Resilience:** Uses dynamic PL/pgSQL block to enable `vector` extension if installed, with clean fallback if pgvector binary is not present in the host environment.
- **Clean Downgrade Execution:** Downgrade drops tables in exact reverse dependency order with `CASCADE`.

---

## 3. Seed Execution Instructions
To apply the complete master schema and seed dataset to a live PostgreSQL 16 database:
```bash
# 1. Run migrations to head
alembic upgrade head

# 2. Apply master demo seed dataset
psql $DATABASE_URL -f database/schema/04-cropsentinel-master-seed.sql
```
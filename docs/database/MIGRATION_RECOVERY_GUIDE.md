# Migration Recovery Guide

## Before any migration

```bash
pg_dump $APP_DATABASE_URL > /tmp/pre-migration.sql
.venv/bin/python -m alembic current
.venv/bin/python -m alembic upgrade head --sql > /tmp/migrations.sql
# Review /tmp/migrations.sql line by line. Forward-only in production.
```

## Restore

```bash
psql $APP_DATABASE_URL < /tmp/pre-migration.sql
.venv/bin/python -m alembic current  # verify revision matches the dump
```

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `CREATE EXTENSION ... syntax error` on SQLite | Extension SQL ran against SQLite | Fixed in 0004 via `_is_postgresql()` gate; upgrade past `0003` |
| `alembic_version` missing but tables exist | DB was built by `init_db` (create_all) | Run drift check; stamp only on full match, else backfill |
| Downgrade `DROP EXTENSION` fails | Non-ORM PostGIS dependency (reference schema/manual geometry) | Keep the extension (inert with no spatial columns); drop tables only |
| FK creation fails on existing DB | Tables created out of dependency order | Re-run `upgrade head` after fixing order; never hand-create tables — go through Alembic |
| `alembic check` reports type diffs | ORM type changed without a revision | Generate + review a revision; never hand-edit a live DB to match ORM |

## Downgrade scope

`0004` downgrade drops its 43 tables in reverse dependency order and leaves
0002/0003 tables untouched. `0003` drops video tables, `0002` drops chat
tables, `0001` is a no-op. Practice on a disposable database:
`upgrade head → downgrade base → upgrade head`.

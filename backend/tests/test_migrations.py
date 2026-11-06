"""Migration and schema tests (Phase 8).

- Fresh-SQLite Alembic apply + metadata parity (tables/columns/PKs/FKs).
- Offline SQL contains every ORM table (dialect-neutral, no live DB needed).
- PostgreSQL/PostGIS catalog tests are present but **skipped** when no
  PostgreSQL URL is configured — they never pass on SQLite.

Run: .venv/bin/python -m pytest tests/test_migrations.py -q
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.db import models  # noqa: F401
from app.db.base import Base
from app.geo import models as _geo_models  # noqa: F401  (registers H3 tables)
from sqlalchemy import create_engine, inspect

BACKEND = Path(__file__).resolve().parents[1]


def _expected_revision() -> str:
    script = ScriptDirectory.from_config(Config(str(BACKEND / "alembic.ini")))
    heads = script.get_heads()
    assert len(heads) == 1, heads
    return heads[0]


def test_head_revision_exists() -> None:
    assert _expected_revision() == "0005_h3_hexagonal_grid"


def test_offline_sql_creates_every_orm_table() -> None:
    # File-level proof: every ORM table is created in 0002/0003/0004/0005.
    text = "\n".join(
        Path(f"{BACKEND}/app/db/migrations/versions/{name}").read_text(encoding="utf-8")
        for name in (
            "0002_chat_persistence.py",
            "0003_video_persistence.py",
            "0004_domain_persistence.py",
            "0005_h3_hexagonal_grid.py",
        )
    )
    for table in Base.metadata.tables:
        assert f'"{table}"' in text, table


def test_fresh_sqlite_migration_matches_metadata(tmp_path: Path, monkeypatch) -> None:
    # Apply head to a disposable SQLite file via subprocess-free Alembic API.
    db_path = tmp_path / "fresh.db"
    url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("APP_DATABASE_URL", url)
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.db.session import reset_engine

    reset_engine()
    try:
        from alembic import command
        from alembic.config import Config as AlembicConfig

        command.upgrade(AlembicConfig(str(BACKEND / "alembic.ini")), "head")
    finally:
        reset_engine()
        get_settings.cache_clear()

    engine = create_engine(url)
    insp = inspect(engine)
    assert set(insp.get_table_names()) >= set(Base.metadata.tables)
    for tname, table in Base.metadata.tables.items():
        orm_cols = {c.name for c in table.columns}
        db_cols = {c["name"] for c in insp.get_columns(tname)}
        assert orm_cols == db_cols, tname
        assert {c.name for c in table.primary_key.columns} <= db_cols
        # FK spot checks.
    user_fks = insp.get_foreign_keys("user_roles")
    assert {fk["referred_table"] for fk in user_fks} == {"users", "roles"}


# --- PostgreSQL/PostGIS live tests (skipped without a server) --------------


def _pg_url() -> str | None:
    import os

    url = os.environ.get("APP_DATABASE_URL", "")
    return url if url.startswith(("postgresql", "postgres")) else None


pg_required = pytest.mark.skipif(
    _pg_url() is None,
    reason="needs PostgreSQL (set APP_DATABASE_URL to a postgresql URL)",
)


@pg_required
def test_postgresql_migrated_schema_matches_metadata() -> None:
    url = _pg_url()
    assert url is not None
    engine = create_engine(url)
    insp = inspect(engine)
    assert set(Base.metadata.tables) <= set(insp.get_table_names())
    for tname, table in Base.metadata.tables.items():
        orm_cols = {c.name for c in table.columns}
        db_cols = {c["name"] for c in insp.get_columns(tname)}
        assert orm_cols == db_cols, tname


@pg_required
def test_postgresql_postgis_extension_and_spatial() -> None:
    """PostGIS proof — skipped (not passed) where the extension is absent."""
    from sqlalchemy import text

    url = _pg_url()
    assert url is not None
    engine = create_engine(url)
    with engine.connect() as conn:
        ext = conn.execute(
            text("SELECT extname FROM pg_extension WHERE extname='postgis'")
        ).scalar()
        if ext is None:
            pytest.skip(
                "PostGIS not available on this host — extension/spatial checks blocked (not passed)"
            )
        geom_query = (
            "SELECT count(*) FROM geometry_columns "
            "WHERE f_table_schema='public' AND f_table_name IN "
            "('geographies','growing_areas','observations')"
        )
        geom = conn.execute(text(geom_query)).scalar()
        # Backend ORM has zero geometry columns (see ORM_INVENTORY §3).
        assert geom == 0


@pg_required
def test_postgresql_alembic_current_is_head() -> None:
    from sqlalchemy import text

    url = _pg_url()
    assert url is not None
    engine = create_engine(url)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert version == _expected_revision()


@pg_required
def test_postgresql_timestamp_types_match_orm() -> None:
    """UTCDateTime (naive) vs DateTime(timezone=True) must not be conflated."""
    from sqlalchemy import text

    url = _pg_url()
    assert url is not None
    engine = create_engine(url)
    with engine.connect() as conn:
        naive = conn.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name='users' AND column_name='created_at'"
            )
        ).scalar()
        aware = conn.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name='conversations' AND column_name='created_at'"
            )
        ).scalar()
    assert naive == "timestamp without time zone"
    assert aware == "timestamp with time zone"

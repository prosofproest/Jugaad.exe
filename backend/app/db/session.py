"""Database engine, session factory and development bootstrap.

Production uses PostgreSQL 16 + PostGIS. Local development and the test suite
run on SQLite with the same SQLAlchemy models so the safety invariants live in
one place. ``init_db`` is only used for local dev and tests; Alembic remains the
schema authority for deployed environments.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _configure_sqlite(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def create_engine_for_url(url: str) -> Engine:
    kwargs: dict[str, object] = {"future": True, "pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):
        _configure_sqlite(engine)
    return engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        if settings.database_url.startswith("sqlite:///"):
            raw_path = settings.database_url.removeprefix("sqlite:///")
            Path(raw_path).parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine_for_url(settings.database_url)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False
        )
    return _SessionLocal


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one transaction-scoped session per request.

    The request is the unit of work. Commits on success and rolls back
    on exception so that flush-only service code (conversations, uploads,
    videos) persists across requests. Routes that already call ``db.commit()``
    explicitly are unaffected: the second commit is a no-op. This mirrors
    the test fixture in ``tests/test_chat_api.py``.
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Alias for compatibility
get_db = get_session


def reset_engine() -> None:
    """Drop cached engine/session factory (used after settings change in tests)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def init_db(*, seed: bool = True) -> None:
    """Create all tables for local dev/test and seed reference data."""
    from app.db import models  # noqa: F401  (registers mappers)
    from app.db.base import Base
    from app.geo import models as _geo_models  # noqa: F401  (registers H3 tables)

    Base.metadata.create_all(bind=get_engine())
    if seed:
        from app.db.seed import seed_reference_data

        with get_session_factory()() as session:
            seed_reference_data(session)
            session.commit()

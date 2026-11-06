"""Database engine and session dependency.

The engine is created lazily so that tests and tools that do not touch a
database never open a connection.
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one transaction-scoped session per request.

    The request commits when it returns and rolls back if it raises, so a
    multi-row turn (user message + assistant reply + event) is atomic.
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

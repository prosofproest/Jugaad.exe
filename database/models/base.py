"""
CropSentinel AI — Base SQLAlchemy Definitions & Type Handlers
Provides:
- Base declarative class
- Timestamp and Soft-Delete mixins
- Portable UUID, PostGIS Geometry, and Vector type decorators
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import CHAR, Column, DateTime, String, Text, TypeDecorator, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid_str() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Base class for all CropSentinel AI SQLAlchemy models."""
    pass


class TimestampMixin:
    """Provides standard audit timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Provides soft deletion support."""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class PortableUUID(TypeDecorator):
    """
    Platform-independent UUID type.
    Uses PostgreSQL's native UUID type, or CHAR(36) on SQLite/other engines.
    """
    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            return str(uuid.UUID(str(value)))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            try:
                return uuid.UUID(str(value))
            except ValueError:
                return value
        return value


class PostGISGeometry(TypeDecorator):
    """
    Portable PostGIS Geometry type decorator.
    Generates 'geometry(Type, SRID)' on PostgreSQL / PostGIS,
    and falls back to TEXT on SQLite/unit testing without binary dependencies.
    """
    impl = Text
    cache_ok = True

    def __init__(self, geometry_type: str = "GEOMETRY", srid: int = 4326, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry_type = geometry_type.upper()
        self.srid = srid

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.types import UserDefinedType

            class PGGeometry(UserDefinedType):
                def __init__(self, gtype, srid):
                    self.gtype = gtype
                    self.srid = srid

                def get_col_spec(self, **kw):
                    return f"geometry({self.gtype}, {self.srid})"

            return dialect.type_descriptor(PGGeometry(self.geometry_type, self.srid))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect) -> Any:
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value: Any, dialect) -> Any:
        return value


class VectorType(TypeDecorator):
    """
    pgvector vector type decorator.
    Compiles to vector(dim) on PostgreSQL with pgvector, falls back to Text/JSON elsewhere.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim: int = 1536, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.types import UserDefinedType

            class PGVector(UserDefinedType):
                def __init__(self, dim):
                    self.dim = dim

                def get_col_spec(self, **kw):
                    return f"vector({self.dim})"

            return dialect.type_descriptor(PGVector(self.dim))
        return dialect.type_descriptor(Text())


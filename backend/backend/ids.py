"""Identifier helpers.

Rows use prefixed, URL-safe identifiers so a log line or an API response can
be read without a lookup table. UUIDs remain the collision-resistant source.
"""

from __future__ import annotations

import uuid


def new_id(prefix: str) -> str:
    """Return a prefixed identifier such as ``fcst_3f2a...``."""

    clean = prefix.strip().lower().replace(" ", "_")
    if not clean:
        raise ValueError("identifier prefix must not be empty")
    return f"{clean}_{uuid.uuid4().hex}"

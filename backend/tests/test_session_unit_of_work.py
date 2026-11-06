"""Regression: the request is the unit of work.

The chat, upload and video repositories only call ``session.flush()`` and leave
the transaction boundary to the API. If ``get_session`` closes without
committing, the ``201`` response still looks correct but the row is gone the
moment the next request opens a new session. This test exercises the *real*
dependency (no override) against a file-backed SQLite database so the commit at
the dependency boundary is what makes the second request see the first one's
write.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from app.core.config import get_settings
from app.db import session as db_session
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture()
def file_database(tmp_path: Path) -> Iterator[None]:
    settings = get_settings()
    previous_url = settings.database_url
    previous_seed = settings.seed_reference_data
    settings.database_url = f"sqlite:///{(tmp_path / 'unit_of_work.db').as_posix()}"
    settings.seed_reference_data = False
    db_session.reset_engine()
    db_session.init_db(seed=False)
    try:
        yield
    finally:
        db_session.reset_engine()
        settings.database_url = previous_url
        settings.seed_reference_data = previous_seed


def test_conversation_created_in_one_request_is_visible_in_the_next(
    file_database: None,
) -> None:
    client = TestClient(app)

    created = client.post("/v1/conversations", json={"title": "Persistence check"})
    assert created.status_code == 201, created.text
    conversation_id = created.json()["conversation_id"]

    # A second request gets a brand-new session. The row is only visible if the
    # first request committed when the dependency finished.
    fetched = client.get(f"/v1/conversations/{conversation_id}")
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["title"] == "Persistence check"

    listed = client.get("/v1/conversations")
    assert listed.status_code == 200, listed.text
    assert [item["conversation_id"] for item in listed.json()] == [conversation_id]

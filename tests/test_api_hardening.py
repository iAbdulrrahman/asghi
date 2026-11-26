"""Persistence and error-shape fixes: repository reuse, 404 instead of 500."""
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from asghi.domain.passage import Passage
from asghi.domain.user import User
from asghi.repository import get_repository
from asghi.seed import seed_database


def test_repository_is_created_once_per_database_path(monkeypatch, tmp_path):
    db = str(tmp_path / "cache.db")
    monkeypatch.setenv("ASGHI_DB_PATH", db)
    first = get_repository()
    second = get_repository()
    assert first is second, "a new Repository per request re-runs the whole DDL each time"

    other_db = str(tmp_path / "other.db")
    monkeypatch.setenv("ASGHI_DB_PATH", other_db)
    assert get_repository() is not first, "each database path keeps its own instance"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = str(tmp_path / "errors.db")
    monkeypatch.setenv("ASGHI_SEED_PASSWORD", "123456")
    monkeypatch.setenv("ASGHI_DB_PATH", db)
    seed_database(db)
    User._registry.clear()
    Passage._registry.clear()
    from asghi.api import app

    with TestClient(app) as c:
        yield c


def test_unknown_question_id_returns_404_not_500(client):
    tok = client.post("/api/auth/login", json={"identifier": "learner@asghi.org", "password": "123456"}).json()["token"]
    h = {"Authorization": f"Bearer {tok}"}
    pid = client.get("/api/passages", headers=h).json()[0]["passageId"]
    sid = client.post("/api/learner/sessions", json={"passageId": pid}, headers=h).json()["sessionId"]

    r = client.post(
        f"/api/learner/sessions/{sid}/answer",
        json={"questionId": str(uuid.uuid4()), "answer": "x"},
        headers=h,
    )
    assert r.status_code == 404, f"expected 404, got {r.status_code}: {r.text[:120]}"

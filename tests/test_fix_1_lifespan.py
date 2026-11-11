"""Test for Item 1: Per-request repository access and FastAPI lifespan hydration.
Must fail before fix is applied.
"""
import os
import pytest
from fastapi.testclient import TestClient

from asghi.domain.enums import UserRole, Level
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.seed import seed_database


def test_lifespan_hydrates_db_into_fresh_app():
    """Verify that launching TestClient with lifespan populates repository and allows login without pre-existing memory."""
    db_test = "test_lifespan.db"
    if os.path.exists(db_test):
        os.remove(db_test)

    # Seed database file directly
    seed_database(db_test)

    # Clear all in-memory registries completely
    User._registry.clear()
    Passage._registry.clear()

    # Import app and point to test db
    os.environ["ASGHI_DB_PATH"] = db_test
    from asghi.api import app

    # Without lifespan hydration, app starts with empty registries and fails login with 401
    with TestClient(app) as client:
        res = client.post("/api/auth/login", json={
            "emailOrPhone": "learner@asghi.org",
            "password": "LearnerPass123!"
        })
        assert res.status_code == 200, f"Expected 200 after lifespan hydration, got {res.status_code}"
        assert "token" in res.json()

    if os.path.exists(db_test):
        os.remove(db_test)

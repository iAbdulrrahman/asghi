import os
import sqlite3
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.seed import seed_database


def test_learner_progress_completed_tests_increments(tmp_path):
    """Fix 14: finished session increments completedTests in GET /api/learner/progress."""
    test_db = str(tmp_path / "test_progress_completed.db")
    seed_database(test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    with TestClient(app) as client:
        # Login as learner
        res = client.post(
            "/api/auth/login",
            json={"identifier": "learner@asghi.org", "password": "LearnerPass123!"}
        )
        assert res.status_code == 200
        token = res.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}

        # Check initial progress
        prog_res = client.get("/api/learner/progress", headers=headers)
        assert prog_res.status_code == 200
        initial_completed = prog_res.json().get("completedTests", 0)

        # Get a verified passage
        cat_res = client.get("/api/passages", headers=headers)
        assert cat_res.status_code == 200
        passages = cat_res.json()
        assert len(passages) > 0
        passage_id = passages[0]["passageId"]

        # Start session
        start_res = client.post(
            "/api/learner/sessions",
            headers=headers,
            json={"passageId": passage_id}
        )
        assert start_res.status_code == 200
        session_id = start_res.json()["sessionId"]

        # Finish session
        finish_res = client.post(
            f"/api/learner/sessions/{session_id}/finish",
            headers=headers
        )
        assert finish_res.status_code == 200

        # Progress endpoint must now report completedTests > initial_completed
        prog_res_after = client.get("/api/learner/progress", headers=headers)
        assert prog_res_after.status_code == 200
        after_completed = prog_res_after.json().get("completedTests", 0)
        assert after_completed == initial_completed + 1

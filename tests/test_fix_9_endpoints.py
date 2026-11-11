"""Tests for Fix Item 9: Endpoint 404 Corrections
Verify /api/admin/generate and /api/contributor/awaiting-recording work correctly
without 404 errors.
"""
import pytest
from fastapi.testclient import TestClient
from asghi.api import app
from asghi.seed import seed_database
import os

def test_admin_generate_and_contributor_awaiting_endpoints(tmp_path):
    test_db = str(tmp_path / "fix9.db")
    seed_database(db_path=test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    with TestClient(app) as client:
        # 1. Admin logs in
        admin_login = client.post("/api/auth/login", json={
            "identifier": "admin@asghi.org",
            "password": "AdminPass123!"
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["accessToken"]

        # 2. Admin calls /api/admin/generate with topic and level (from mobile screen)
        gen_res = client.post(
            "/api/admin/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"topic": "العلوم الحديثة", "level": "B1"}
        )
        assert gen_res.status_code == 200
        gen_data = gen_res.json()
        assert "passageId" in gen_data
        assert gen_data.get("topic") == "العلوم الحديثة"
        assert gen_data.get("questionsCount") == 3

        # 3. Contributor logs in
        con_login = client.post("/api/auth/login", json={
            "identifier": "contributor@asghi.org",
            "password": "ContributorPass123!"
        })
        assert con_login.status_code == 200
        con_token = con_login.json()["accessToken"]

        # 4. Contributor gets awaiting recording
        awaiting_res = client.get(
            "/api/contributor/awaiting-recording",
            headers={"Authorization": f"Bearer {con_token}"}
        )
        assert awaiting_res.status_code == 200
        passages = awaiting_res.json()
        assert isinstance(passages, list)

"""Acceptance test for P0 Item 4 and P3 Item 11:
Seed in a subprocess -> a NEW process / lifespan logs in (200) and sees seeded passages.
"""
import os
import subprocess
import sys
import pytest
from fastapi.testclient import TestClient


def test_seed_and_restart_persistence(tmp_path):
    test_db = str(tmp_path / "acceptance_restart.db")

    # Step 1: Seed in an independent subprocess
    seed_cmd = [
        sys.executable,
        "seed.py",
        test_db,
    ]
    env = os.environ.copy()
    env["ASGHI_DB_PATH"] = test_db
    res = subprocess.run(seed_cmd, env=env, capture_output=True, text=True, check=True)
    assert "Seed completed successfully" in res.stdout
    assert os.path.exists(test_db)

    # Step 2: Fresh client in this process configured with the seeded database
    os.environ["ASGHI_DB_PATH"] = test_db
    # Clear any leftover memory registries to simulate clean startup
    from asghi.domain.user import User
    from asghi.domain.passage import Passage
    User._registry.clear()
    Passage._registry.clear()

    from asghi.api import app
    with TestClient(app) as client:
        # Step 3: Login as seeded learner via real credentials
        login_res = client.post(
            "/api/auth/login",
            json={"identifier": "learner@asghi.org", "password": "LearnerPass123!"}
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        data = login_res.json()
        assert "accessToken" in data
        token = data["accessToken"]

        # Step 4: Access role-gated passages catalogue
        passages_res = client.get(
            "/api/passages",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert passages_res.status_code == 200, f"Browse failed: {passages_res.text}"
        passages_data = passages_res.json()
        passages = passages_data if isinstance(passages_data, list) else passages_data.get("passages", [])
        assert len(passages) >= 1
        assert any("تَمْتَازُ" in p["text"] or "اللغة" in p["text"] or "العربية" in p["text"] for p in passages)

        # Step 5: Login as seeded admin
        admin_login = client.post(
            "/api/auth/login",
            json={"identifier": "admin@asghi.org", "password": "AdminPass123!"}
        )
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["accessToken"]

        # Check dashboard
        dash_res = client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert dash_res.status_code == 200
        dash_data = dash_res.json()
        assert len(dash_data["users"]) >= 4
        assert dash_data["report"]["totalPassages"] >= 3

"""Auth & Profile API tests: Req 1.2, 1.3.
"""
import pytest
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.domain.enums import UserRole, Level
from asghi.domain.user import User

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_registry():
    User._registry.clear()
    yield
    User._registry.clear()


def test_register_and_login_email_or_phone():
    """Req 1.2: Users can register and sign in with email or phone number."""
    # 1. Register with email
    r1 = client.post("/api/auth/register", json={
        "emailOrPhone": "learner1@asghi.org",
        "password": "Password123!"
    })
    assert r1.status_code == 201
    assert "token" in r1.json()

    # Login with email
    l1 = client.post("/api/auth/login", json={
        "emailOrPhone": "learner1@asghi.org",
        "password": "Password123!"
    })
    assert l1.status_code == 200
    assert "token" in l1.json()

    # 2. Register with phone number
    r2 = client.post("/api/auth/register", json={
        "emailOrPhone": "+966501234567",
        "password": "PhonePassword123!"
    })
    assert r2.status_code == 201

    # Login with phone number
    l2 = client.post("/api/auth/login", json={
        "emailOrPhone": "+966501234567",
        "password": "PhonePassword123!"
    })
    assert l2.status_code == 200
    assert "token" in l2.json()

    # Bad login
    l_bad = client.post("/api/auth/login", json={
        "emailOrPhone": "learner1@asghi.org",
        "password": "WrongPassword!"
    })
    assert l_bad.status_code == 401


def test_complete_profile():
    """Req 1.3: New users complete a short profile: display name, Arabic level (A1-C2), role interest."""
    r = client.post("/api/auth/register", json={
        "emailOrPhone": "newuser@asghi.org",
        "password": "Password123!"
    })
    token = r.json()["token"]

    p_res = client.post(
        "/api/users/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "displayName": "فاطمة اللغوية",
            "level": "B2",
            "roleInterest": "CONTRIBUTOR"
        }
    )
    assert p_res.status_code == 200
    data = p_res.json()
    assert data["displayName"] == "فاطمة اللغوية"
    assert data["arabicLevel"] == "B2"
    assert "CONTRIBUTOR" in data["roles"]

    # Verify profile via /api/users/me
    me_res = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me = me_res.json()
    assert me["displayName"] == "فاطمة اللغوية"
    assert me["arabicLevel"] == "B2"

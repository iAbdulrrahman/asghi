"""Admin Governance & Reporting API tests: Req 10, 10.1, 10.2.
"""
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.domain.enums import UserRole, Level, FlagStatus
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.security import create_access_token

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_registry():
    User._registry.clear()
    Passage._registry.clear()
    yield
    User._registry.clear()
    Passage._registry.clear()


def test_admin_governance_and_moderation():
    """Req 10: Admins shall be able to govern content, users, and reputation."""
    admin = User(email="admin_gov@asghi.org")
    admin.addRole(UserRole.ADMIN)
    token = create_access_token(admin.userId, [UserRole.ADMIN])

    # Manage user status
    target_user = User(email="target@asghi.org")
    target_user.addRole(UserRole.LEARNER)

    m_res = client.post(
        f"/api/admin/users/{target_user.userId}/manage",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "SUSPENDED"}
    )
    assert m_res.status_code == 200
    assert target_user.status == "SUSPENDED"


def test_contributor_and_reviewer_reputation():
    """Req 10.1: Reputation system for Contributors and Reviewers."""
    con = User(email="con_rep@asghi.org")
    cp = con.addRole(UserRole.CONTRIBUTOR)
    cp.reputation.recordSubmissionResult(True)
    cp.reputation.recordSubmissionResult(True)
    cp.reputation.recordSubmissionResult(False)

    res = client.get(f"/api/users/{con.userId}/reputation")
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "CONTRIBUTOR"
    assert data["totalSubmissions"] == 3
    assert data["approvalRate"] == 0.67
    assert data["score"] == 115  # 100 + 10 + 10 - 5


def test_admin_dashboard_and_reporting():
    """Req 10.2: Admin dashboard for moderation, user management, AI generation, and reporting."""
    admin = User(email="admin_dash@asghi.org")
    admin.addRole(UserRole.ADMIN)
    token = create_access_token(admin.userId, [UserRole.ADMIN])

    # Dashboard endpoint
    d_res = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert d_res.status_code == 200
    dash = d_res.json()
    assert "report" in dash
    assert "users" in dash
    assert dash["report"]["totalUsers"] >= 1

    # Report endpoint
    r_res = client.get("/api/admin/report?period=MONTHLY", headers={"Authorization": f"Bearer {token}"})
    assert r_res.status_code == 200
    assert r_res.json()["period"] == "MONTHLY"

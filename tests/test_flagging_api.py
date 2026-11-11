"""Content Flagging API tests: Req 6.7.
"""
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.domain.enums import UserRole, Level, ContentStatus, FlagStatus
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


def test_flag_problematic_content():
    """Req 6.7: Learners can flag question or audio as problematic, and Admin resolves it."""
    learner = User(email="learner_flag@asghi.org")
    learner.addRole(UserRole.LEARNER)
    l_token = create_access_token(learner.userId, [UserRole.LEARNER])

    admin = User(email="admin_flag@asghi.org")
    admin.addRole(UserRole.ADMIN)
    a_token = create_access_token(admin.userId, [UserRole.ADMIN])

    p = Passage(
        text="نص لغوي يحتوي على خطأ مطبعي",
        level=Level.B1,
        topic="عام",
        duration=timedelta(seconds=60),
    )

    # 1. Learner flags content
    f_res = client.post(
        "/api/learner/flag",
        headers={"Authorization": f"Bearer {l_token}"},
        json={"contentId": str(p.passageId), "reason": "خطأ مطبعي في الفقرة الأولى"}
    )
    assert f_res.status_code == 200
    flag_id = f_res.json()["flagId"]

    # 2. Admin views flags list
    list_res = client.get("/api/admin/flags", headers={"Authorization": f"Bearer {a_token}"})
    assert list_res.status_code == 200
    assert any(f["flagId"] == flag_id for f in list_res.json())

    # 3. Admin resolves flag with ACTION_TAKEN -> content becomes FLAGGED
    res_res = client.post(
        f"/api/admin/flags/{flag_id}/resolve",
        headers={"Authorization": f"Bearer {a_token}"},
        json={"newState": "ACTION_TAKEN"}
    )
    assert res_res.status_code == 200
    assert p.status == ContentStatus.FLAGGED

"""Passage Catalogue API tests: Req 2.
"""
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.domain.enums import UserRole, Level, ContentStatus, Origin
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


def test_catalogue_maintenance():
    """Req 2: Maintain catalogue of listening passages, text, audio, and questions."""
    admin = User(email="admin_cat@asghi.org")
    admin.addRole(UserRole.ADMIN)
    token = create_access_token(admin.userId, [UserRole.ADMIN])

    # 1. Admin creates catalogue passage
    res = client.post(
        "/api/admin/passages",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "تعد القراءة والاستماع من أهم مهارات اكتساب اللغة العربية الفصحى في العصر الحديث.",
            "level": "B1",
            "topic": "التعليم",
            "durationSeconds": 90,
            "origin": "HUMAN"
        }
    )
    assert res.status_code == 200
    p_id = res.json()["passageId"]

    # 2. Browse catalogue
    browse_res = client.get("/api/passages?level=B1&topic=التعليم")
    assert browse_res.status_code == 200
    passages = browse_res.json()
    assert len(passages) >= 1
    assert passages[0]["passageId"] == p_id
    assert passages[0]["level"] == "B1"
    assert passages[0]["topic"] == "التعليم"

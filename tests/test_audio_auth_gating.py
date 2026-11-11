"""Test verifying audio endpoint authentication gating (Bearer header & ?token= query).
"""
import os
import pytest
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.seed import seed_database
from asghi.domain.enums import UserRole
from asghi.security import create_access_token
from asghi.domain.user import User

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_seed(tmp_path):
    db_path = str(tmp_path / "test_audio_auth.db")
    seed_database(db_path=db_path)


def test_audio_endpoint_requires_auth():
    # 1. No token -> 401
    res = client.get("/api/audio/sample_fusha_01.mp3")
    assert res.status_code == 401, f"Expected 401 Unauthorized without token, got {res.status_code}"

    # 2. Invalid token in header -> 401
    res = client.get("/api/audio/sample_fusha_01.mp3", headers={"Authorization": "Bearer invalid.token.value"})
    assert res.status_code == 401

    # 3. Invalid token in query -> 401
    res = client.get("/api/audio/sample_fusha_01.mp3?token=invalid.token.value")
    assert res.status_code == 401


def test_audio_endpoint_accepts_bearer_and_query_token():
    learner = next((u for u in User._registry if u.email == "learner@asghi.org"), None)
    assert learner is not None
    token = create_access_token(learner.userId, [UserRole.LEARNER])

    # 1. Valid Bearer header -> 200 + audio content
    res_header = client.get("/api/audio/sample_fusha_01.mp3", headers={"Authorization": f"Bearer {token}"})
    assert res_header.status_code == 200
    assert len(res_header.content) > 0
    assert res_header.headers.get("content-type") == "audio/mpeg"

    # 2. Valid query param token -> 200 + audio content
    res_query = client.get(f"/api/audio/sample_fusha_01.mp3?token={token}")
    assert res_query.status_code == 200
    assert len(res_query.content) > 0
    assert res_query.headers.get("content-type") == "audio/mpeg"


def test_inventions_documents_audio_auth_gating():
    inventions_path = os.path.join(os.path.dirname(__file__), "..", "INVENTIONS.md")
    with open(inventions_path, "r", encoding="utf-8") as f:
        doc = f.read()
    assert "Audio Endpoint Authentication Gating" in doc or "audio auth gating" in doc.lower(), "INVENTIONS.md must document audio authentication gating"
    assert "?token=" in doc or "token query param" in doc.lower(), "INVENTIONS.md must document the ?token= query parameter choice"


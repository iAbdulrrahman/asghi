"""Boundary hardening: path traversal, session ownership, answer-key exposure.

Each test here fails against the pre-fix API: the traversal returned the SQLite file,
a second learner could drive the first learner's session, and the offline package
served correctAnswer to anonymous callers.
"""
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from asghi.domain.passage import Passage
from asghi.domain.user import User
from asghi.seed import seed_database


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = str(tmp_path / "boundary.db")
    monkeypatch.setenv("ASGHI_SEED_PASSWORD", "123456")
    monkeypatch.setenv("ASGHI_DB_PATH", db)
    seed_database(db)
    User._registry.clear()
    Passage._registry.clear()
    from asghi.api import app

    with TestClient(app) as c:
        yield c


def _token(client, ident="learner@asghi.org"):
    r = client.post("/api/auth/login", json={"identifier": ident, "password": "123456"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _second_learner(client):
    r = client.post("/api/auth/register", json={"emailOrPhone": "other@asghi.org", "password": "123456"})
    assert r.status_code == 201, r.text
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    p = client.post("/api/users/profile",
                    json={"displayName": "Other", "level": "A1", "roleInterest": "LEARNER"}, headers=h)
    assert p.status_code == 200, p.text
    return _token(client, "other@asghi.org")


def test_audio_endpoint_cannot_escape_upload_dir(client):
    h = _token(client)
    for attack in ["..%5C..%5Casghi.db", "..%2F..%2Fasghi.db", "..%5C..%5Cseed.py"]:
        r = client.get(f"/api/audio/{attack}", headers=h)
        assert r.status_code == 404, f"{attack} served {len(r.content)} bytes"
        assert b"SQLite format 3" not in r.content


def test_audio_endpoint_still_serves_real_files(client):
    from asghi.api import UPLOAD_DIR

    name = f"test_{uuid.uuid4().hex}.wav"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as f:
        f.write(b"RIFF" + b"\x00" * 40)
    try:
        r = client.get(f"/api/audio/{name}", headers=_token(client))
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("audio/")
    finally:
        os.remove(path)


def test_other_learner_cannot_read_or_finish_a_session(client):
    h1 = _token(client)
    pid = client.get("/api/passages", headers=h1).json()[0]["passageId"]
    sid = client.post("/api/learner/sessions", json={"passageId": pid}, headers=h1).json()["sessionId"]

    h2 = _second_learner(client)
    assert client.get(f"/api/learner/sessions/{sid}/question", headers=h2).status_code == 404
    assert client.post(f"/api/learner/sessions/{sid}/answer",
                       json={"questionId": str(uuid.uuid4()), "answer": "x"}, headers=h2).status_code == 404
    assert client.post(f"/api/learner/sessions/{sid}/finish", headers=h2).status_code == 404

    # the owner still works
    assert client.get(f"/api/learner/sessions/{sid}/question", headers=h1).status_code == 200


def test_offline_package_requires_auth_and_hides_the_answer_key(client):
    pid = client.get("/api/passages").json()[0]["passageId"]
    anon = client.get(f"/api/passages/{pid}/offline-package")
    assert anon.status_code in (401, 403)

    r = client.get(f"/api/passages/{pid}/offline-package", headers=_token(client))
    assert r.status_code == 200
    body = r.json()
    assert body["questions"], "package should still list questions"
    for q in body["questions"]:
        assert "correctAnswer" not in q
        assert "explanation" not in q

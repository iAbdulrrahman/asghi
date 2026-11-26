"""Upload rules: a claim is required, and length is measured, not believed.

Fails against the pre-fix API: submit-audio accepted an unclaimed passage (200) and
trusted the client's durationSeconds for any non-WAV upload.
"""
import pytest
from fastapi.testclient import TestClient

from asghi.domain.passage import Passage
from asghi.domain.user import User
from asghi.seed import seed_database


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = str(tmp_path / "upload.db")
    monkeypatch.setenv("ASGHI_SEED_PASSWORD", "123456")
    monkeypatch.setenv("ASGHI_DB_PATH", db)
    seed_database(db)
    User._registry.clear()
    Passage._registry.clear()
    from asghi.api import app

    with TestClient(app) as c:
        yield c


def _contributor(client):
    r = client.post("/api/auth/login", json={"identifier": "contributor@asghi.org", "password": "123456"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _mp3(seconds):
    """A syntactically valid MPEG-1 Layer III stream: 128 kbps, 44.1 kHz, 417-byte frames."""
    frame = b"\xff\xfb\x90\x64" + b"\x00" * 413
    frames = int(round(seconds / (1152 / 44100)))
    return frame * frames


def test_upload_requires_an_active_claim(client):
    h = _contributor(client)
    pid = client.get("/api/contributor/awaiting-recording", headers=h).json()[0]["passageId"]
    r = client.post(
        "/api/contributor/submit-audio",
        data={"passageId": pid, "durationSeconds": "90"},
        files={"file": ("a.mp3", _mp3(90), "audio/mpeg")},
        headers=h,
    )
    assert r.status_code == 409, r.text


def test_claimed_upload_measures_the_file_not_the_form_field(client):
    h = _contributor(client)
    pid = client.get("/api/contributor/awaiting-recording", headers=h).json()[0]["passageId"]
    assert client.post("/api/contributor/claim", json={"passageId": pid}, headers=h).status_code == 200

    short = client.post(
        "/api/contributor/submit-audio",
        data={"passageId": pid, "durationSeconds": "90"},       # lies about the length
        files={"file": ("a.mp3", _mp3(5), "audio/mpeg")},
        headers=h,
    )
    assert short.status_code == 400, f"a 5 s file accepted as 90 s: {short.text}"
    assert "قصيرة" in short.json()["detail"]


def test_claimed_upload_accepts_a_real_length(client):
    h = _contributor(client)
    pid = client.get("/api/contributor/awaiting-recording", headers=h).json()[0]["passageId"]
    assert client.post("/api/contributor/claim", json={"passageId": pid}, headers=h).status_code == 200

    ok = client.post(
        "/api/contributor/submit-audio",
        data={"passageId": pid, "durationSeconds": "90"},
        files={"file": ("a.mp3", _mp3(90), "audio/mpeg")},
        headers=h,
    )
    assert ok.status_code == 200, ok.text

"""Failing test for P0 Item 1:
GET /api/passages must return a ready audioUrl (/api/audio/<audio_file>) per recording.
"""
import pytest
from fastapi.testclient import TestClient
from asghi.api import app
from asghi.seed import seed_database
import os

def test_passages_return_ready_audio_url(tmp_path):
    test_db = str(tmp_path / "test_audio_url.db")
    seed_database(test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    with TestClient(app) as client:
        resp = client.get("/api/passages")
        assert resp.status_code == 200
        passages = resp.json()
        assert len(passages) > 0

        # Find a passage with audio recordings
        found_recording = False
        for p in passages:
            for rec in p.get("audioRecordings", []):
                found_recording = True
                assert "audioUrl" in rec, f"audioUrl missing from recording: {rec}"
                assert rec["audioUrl"] is not None
                assert rec["audioUrl"].startswith("/api/audio/"), f"audioUrl must start with /api/audio/, got: {rec['audioUrl']}"

        assert found_recording, "At least one recording must be present in seeded passages"

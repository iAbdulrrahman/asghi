import io
import os
import sqlite3
import struct
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.seed import seed_database


def make_test_wav(duration_seconds: int, sample_rate: int = 8000) -> bytes:
    """Generate minimal valid PCM WAV bytes."""
    num_channels = 1
    bits_per_sample = 16
    bytes_per_sample = bits_per_sample // 8
    num_samples = sample_rate * duration_seconds
    data_size = num_samples * num_channels * bytes_per_sample
    header_size = 44

    header = bytearray()
    header.extend(b"RIFF")
    header.extend(struct.pack("<I", 36 + data_size))
    header.extend(b"WAVE")
    header.extend(b"fmt ")
    header.extend(struct.pack("<I", 16))  # Subchunk1Size
    header.extend(struct.pack("<H", 1))   # PCM format
    header.extend(struct.pack("<H", num_channels))
    header.extend(struct.pack("<I", sample_rate))
    byte_rate = sample_rate * num_channels * bytes_per_sample
    header.extend(struct.pack("<I", byte_rate))
    block_align = num_channels * bytes_per_sample
    header.extend(struct.pack("<H", block_align))
    header.extend(struct.pack("<H", bits_per_sample))
    header.extend(b"data")
    header.extend(struct.pack("<I", data_size))

    return bytes(header) + (b"\x00" * data_size)


def test_reject_short_audio_even_if_client_claims_valid_duration(tmp_path):
    """Fix 15: Server validates actual audio duration from file header, rejecting short audio (<60s)."""
    test_db = str(tmp_path / "test_duration_validation.db")
    seed_database(test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    with TestClient(app) as client:
        # Login contributor
        con_login = client.post(
            "/api/auth/login",
            json={"identifier": "contributor@asghi.org", "password": "ContributorPass123!"}
        )
        assert con_login.status_code == 200
        con_token = con_login.json()["accessToken"]
        con_headers = {"Authorization": f"Bearer {con_token}"}

        # Find awaiting recording passage
        awaiting = client.get("/api/contributor/awaiting-recording", headers=con_headers).json()
        assert len(awaiting) > 0
        passage_id = awaiting[0]["passageId"]

        # Claim passage
        claim_res = client.post(
            "/api/contributor/claim",
            headers=con_headers,
            json={"passageId": passage_id}
        )
        assert claim_res.status_code == 200

        # Upload a 5-second WAV claiming 60.0 seconds
        short_wav = make_test_wav(duration_seconds=5)
        upload_res = client.post(
            "/api/contributor/submit-audio",
            headers=con_headers,
            data={
                "passageId": passage_id,
                "attribution": "SHOW_NAME",
                "durationSeconds": 60.0,
            },
            files={"file": ("short5.wav", io.BytesIO(short_wav), "audio/wav")}
        )
        # Must be rejected because actual audio is 5s (< 60s)
        assert upload_res.status_code == 400


def test_override_client_duration_with_actual_file_duration(tmp_path):
    """Fix 15: Server derives actual duration (75s) from WAV header and persists it."""
    test_db = str(tmp_path / "test_duration_override.db")
    seed_database(test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    with TestClient(app) as client:
        # Login contributor
        con_login = client.post(
            "/api/auth/login",
            json={"identifier": "contributor@asghi.org", "password": "ContributorPass123!"}
        )
        assert con_login.status_code == 200
        con_token = con_login.json()["accessToken"]
        con_headers = {"Authorization": f"Bearer {con_token}"}

        # Find awaiting recording passage
        awaiting = client.get("/api/contributor/awaiting-recording", headers=con_headers).json()
        assert len(awaiting) > 0
        passage_id = awaiting[0]["passageId"]

        # Claim passage
        claim_res = client.post(
            "/api/contributor/claim",
            headers=con_headers,
            json={"passageId": passage_id}
        )
        assert claim_res.status_code == 200

        # Upload a 75-second WAV claiming 60.0 seconds
        wav_75s = make_test_wav(duration_seconds=75)
        upload_res = client.post(
            "/api/contributor/submit-audio",
            headers=con_headers,
            data={
                "passageId": passage_id,
                "attribution": "SHOW_NAME",
                "durationSeconds": 60.0,
            },
            files={"file": ("real75.wav", io.BytesIO(wav_75s), "audio/wav")}
        )
        assert upload_res.status_code == 200

        # Check in DB that duration_seconds is 75.0, not 60.0
        with sqlite3.connect(test_db) as conn:
            conn.row_factory = sqlite3.Row
            rec = conn.execute(
                "SELECT duration_seconds FROM audio_recordings WHERE passage_id = ?",
                (passage_id,)
            ).fetchone()
            assert rec is not None
            assert round(rec["duration_seconds"]) == 75

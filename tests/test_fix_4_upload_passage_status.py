import io
import os
import sqlite3
from uuid import uuid4
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.domain.enums import ContentStatus
from asghi.domain.passage import Passage
from asghi.seed import seed_database


def generate_wav_bytes(duration_seconds: int = 70, sample_rate: int = 8000) -> bytes:
    num_samples = sample_rate * duration_seconds
    data_size = num_samples * 2
    byte_rate = sample_rate * 2
    block_align = 2
    bits_per_sample = 16
    riff_chunk_size = 36 + data_size

    header = bytearray()
    header.extend(b"RIFF")
    header.extend(riff_chunk_size.to_bytes(4, "little"))
    header.extend(b"WAVE")
    header.extend(b"fmt ")
    header.extend((16).to_bytes(4, "little"))
    header.extend((1).to_bytes(2, "little"))
    header.extend((1).to_bytes(2, "little"))
    header.extend(sample_rate.to_bytes(4, "little"))
    header.extend(byte_rate.to_bytes(4, "little"))
    header.extend(block_align.to_bytes(2, "little"))
    header.extend(bits_per_sample.to_bytes(2, "little"))
    header.extend(b"data")
    header.extend(data_size.to_bytes(4, "little"))

    samples = b"\x00\x00" * num_samples
    return bytes(header + samples)


def test_upload_transitions_passage_to_pending_review_and_clears_active_claim(tmp_path):
    test_db = str(tmp_path / "test_upload_status.db")
    seed_database(test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    with TestClient(app) as client:
        # 1. Login as contributor
        con_login = client.post(
            "/api/auth/login",
            json={"identifier": "contributor@asghi.org", "password": "ContributorPass123!"}
        )
        assert con_login.status_code == 200
        con_token = con_login.json()["accessToken"]
        con_headers = {"Authorization": f"Bearer {con_token}"}

        # 2. Get awaiting-recording passage and claim it
        awaiting_res = client.get("/api/contributor/awaiting-recording", headers=con_headers)
        assert awaiting_res.status_code == 200
        awaiting = awaiting_res.json()
        assert len(awaiting) >= 1
        passage_id = awaiting[0]["passageId"]

        claim_res = client.post(
            "/api/contributor/claim",
            headers=con_headers,
            json={"passageId": passage_id}
        )
        assert claim_res.status_code == 200

        # Verify DB has active claim before upload
        with sqlite3.connect(test_db) as conn:
            c = conn.execute("SELECT count(*) FROM active_claims WHERE passage_id = ?", (passage_id,)).fetchone()[0]
            assert c == 1, "active_claims should have 1 row after claim"

        # 3. Submit real audio
        wav_bytes = generate_wav_bytes(duration_seconds=70)
        upload_res = client.post(
            "/api/contributor/submit-audio",
            headers=con_headers,
            data={"passageId": passage_id, "attribution": "SHOW_NAME", "durationSeconds": 70.0},
            files={"file": ("recording.wav", io.BytesIO(wav_bytes), "audio/wav")},
        )
        assert upload_res.status_code == 200

        # 4. Verify passage status in DB and memory is PENDING_REVIEW, not CLAIMED
        with sqlite3.connect(test_db) as conn:
            conn.row_factory = sqlite3.Row
            p_row = conn.execute("SELECT status, claimed_by FROM passages WHERE passage_id = ?", (passage_id,)).fetchone()
            assert p_row["status"] == "PENDING_REVIEW", f"Passage status in DB should be PENDING_REVIEW, got {p_row['status']}"
            assert p_row["claimed_by"] is None, "claimed_by should be NULL after upload"

            claim_cnt = conn.execute("SELECT count(*) FROM active_claims WHERE passage_id = ?", (passage_id,)).fetchone()[0]
            assert claim_cnt == 0, f"active_claims row should be deleted after upload, found {claim_cnt}"

        # 5. Verify in memory
        mem_p = next(p for p in Passage._registry if str(p.passageId) == passage_id)
        assert mem_p.status == ContentStatus.PENDING_REVIEW
        assert mem_p.claimedBy is None

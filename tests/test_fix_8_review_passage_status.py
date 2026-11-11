import io
import os
import sqlite3
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


def test_positive_review_transitions_passage_to_verified_and_appears_in_catalogue(tmp_path):
    test_db = str(tmp_path / "test_review_status.db")
    seed_database(test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    with TestClient(app) as client:
        # 1. Contributor claims awaiting passage and uploads audio
        con_login = client.post(
            "/api/auth/login",
            json={"identifier": "contributor@asghi.org", "password": "ContributorPass123!"}
        )
        assert con_login.status_code == 200
        con_token = con_login.json()["accessToken"]
        con_headers = {"Authorization": f"Bearer {con_token}"}

        awaiting = client.get("/api/contributor/awaiting-recording", headers=con_headers).json()
        assert len(awaiting) >= 1
        passage_id = awaiting[0]["passageId"]

        client.post("/api/contributor/claim", headers=con_headers, json={"passageId": passage_id})

        wav_bytes = generate_wav_bytes(duration_seconds=70)
        upload_res = client.post(
            "/api/contributor/submit-audio",
            headers=con_headers,
            data={"passageId": passage_id, "attribution": "SHOW_NAME", "durationSeconds": 70.0},
            files={"file": ("recording.wav", io.BytesIO(wav_bytes), "audio/wav")},
        )
        assert upload_res.status_code == 200
        recording_id = upload_res.json()["recordingId"]

        # Before review, learner catalogue should NOT contain this passage
        cat_before = client.get("/api/passages").json()
        assert passage_id not in [p["passageId"] for p in cat_before]

        # 2. Specialist Reviewer approves the recording
        rev_login = client.post(
            "/api/auth/login",
            json={"identifier": "reviewer@asghi.org", "password": "ReviewerPass123!"}
        )
        assert rev_login.status_code == 200
        rev_token = rev_login.json()["accessToken"]
        rev_headers = {"Authorization": f"Bearer {rev_token}"}

        as_res = client.post(
            "/api/reviewer/assignments",
            headers=rev_headers,
            json={"contentId": recording_id}
        )
        assert as_res.status_code == 200
        assignment_id = as_res.json()["assignmentId"]

        dec_res = client.post(
            "/api/reviewer/decision",
            headers=rev_headers,
            json={
                "assignmentId": assignment_id,
                "isApproved": True,
                "reason": "قراءة فصيحة ومتقنة",
                "isFusha": True,
                "dialectFree": True,
                "audioQuality": 5,
            }
        )
        assert dec_res.status_code == 200

        # 3. Verify passage status is VERIFIED in DB and memory
        with sqlite3.connect(test_db) as conn:
            conn.row_factory = sqlite3.Row
            p_row = conn.execute("SELECT status FROM passages WHERE passage_id = ?", (passage_id,)).fetchone()
            assert p_row["status"] == "VERIFIED", f"Expected VERIFIED in DB, got {p_row['status']}"

        mem_p = next(p for p in Passage._registry if str(p.passageId) == passage_id)
        assert mem_p.status == ContentStatus.VERIFIED

        # 4. Learner catalogue MUST now contain this passage with verified audio
        cat_after = client.get("/api/passages").json()
        matching = [p for p in cat_after if p["passageId"] == passage_id]
        assert len(matching) == 1, "Approved passage must appear in learner catalogue"
        assert matching[0]["verifiedAudioCount"] >= 1

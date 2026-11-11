import io
import os
from uuid import uuid4
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.seed import seed_database
from asghi.domain.enums import UserRole
from asghi.domain.user import User


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


def test_contributor_submissions_visible_and_shows_rejection_reason(tmp_path):
    test_db = str(tmp_path / "test_submissions.db")
    seed_database(test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    with TestClient(app) as client:
        # 1. Login as seeded contributor
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
        awaiting_passages = awaiting_res.json()
        assert len(awaiting_passages) >= 1
        passage_id = awaiting_passages[0]["passageId"]

        claim_res = client.post(
            "/api/contributor/claim",
            headers=con_headers,
            json={"passageId": passage_id}
        )
        assert claim_res.status_code == 200

        # 3. Submit real audio
        wav_bytes = generate_wav_bytes(duration_seconds=70)
        upload_res = client.post(
            "/api/contributor/submit-audio",
            headers=con_headers,
            data={"passageId": passage_id, "attribution": "SHOW_NAME", "durationSeconds": 70.0},
            files={"file": ("recording.wav", io.BytesIO(wav_bytes), "audio/wav")},
        )
        assert upload_res.status_code == 200
        recording_id = upload_res.json()["recordingId"]

        # 4. Check /api/contributor/submissions: MUST contain this submission in PENDING_REVIEW
        subs_res = client.get("/api/contributor/submissions", headers=con_headers)
        assert subs_res.status_code == 200
        submissions = subs_res.json()
        matching = [s for s in submissions if s["recordingId"] == recording_id]
        assert len(matching) == 1, "Uploaded recording must be listed in contributor submissions"
        sub = matching[0]
        assert sub["status"] == "PENDING_REVIEW"
        assert sub["passageId"] == passage_id

        # 5. Reviewer rejects the submission
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

        rejection_reason = "نطق غير دقيق لحرف الضاد"
        dec_res = client.post(
            "/api/reviewer/decision",
            headers=rev_headers,
            json={
                "assignmentId": assignment_id,
                "isApproved": False,
                "reason": rejection_reason,
                "isFusha": True,
                "dialectFree": True,
                "audioQuality": 3,
            }
        )
        assert dec_res.status_code == 200

        # 6. Check /api/contributor/submissions: MUST show REJECTED with rejectionReason
        subs_res2 = client.get("/api/contributor/submissions", headers=con_headers)
        assert subs_res2.status_code == 200
        submissions2 = subs_res2.json()
        matching2 = [s for s in submissions2 if s["recordingId"] == recording_id]
        assert len(matching2) == 1
        sub2 = matching2[0]
        assert sub2["status"] == "REJECTED"
        assert sub2["rejectionReason"] == rejection_reason

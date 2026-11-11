"""P1 Item 8 Acceptance Test:
1. Contributor records/provides real WAV audio and uploads it to /api/contributor/submit-audio.
2. Backend row exists in database with real byte size and matching file on disk.
3. Reviewer retrieves pending recording, streams audio file, and submits APPROVED verdict.
4. Content transitions to VERIFIED with verified audio available for Learner playback.
"""
import io
import os
import struct
import pytest
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.repository import Repository
from asghi.domain.enums import UserRole, Level, ContentStatus


def generate_wav_bytes(duration_seconds: int = 60, sample_rate: int = 44100) -> bytes:
    """Generate a standard 16-bit mono PCM WAV file byte stream."""
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
    block_align = num_channels * (bits_per_sample // 8)
    data_size = sample_rate * duration_seconds * (bits_per_sample // 8)

    # 44-byte header
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,  # Subchunk1Size
        1,   # AudioFormat (PCM)
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    # Silent PCM data
    pcm_data = b"\x00" * data_size
    return header + pcm_data


def test_contributor_upload_real_audio_and_playback_lifecycle(tmp_path):
    from asghi.seed import seed_database
    test_db = str(tmp_path / "acceptance_audio.db")
    seed_database(db_path=test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    with TestClient(app) as client:
        # 1. Login as contributor
        login_con = client.post(
            "/api/auth/login",
            json={"identifier": "contributor@asghi.org", "password": "ContributorPass123!"}
        )
        assert login_con.status_code == 200
        con_token = login_con.json()["accessToken"]

        # 2. Get awaiting recording passages
        awaiting_res = client.get(
            "/api/contributor/awaiting-recording",
            headers={"Authorization": f"Bearer {con_token}"}
        )
        assert awaiting_res.status_code == 200
        passages = awaiting_res.json()
        assert len(passages) > 0
        passage = passages[0]
        passage_id = passage["passageId"]

        # 3. Claim the passage
        claim_res = client.post(
            "/api/contributor/claim",
            headers={"Authorization": f"Bearer {con_token}"},
            json={"passageId": passage_id}
        )
        assert claim_res.status_code == 200

        # 4. Generate real 60-second WAV audio bytes
        wav_bytes = generate_wav_bytes(duration_seconds=60)
        expected_size = len(wav_bytes)
        assert expected_size == 44 + 44100 * 2 * 60

        # 5. Upload actual binary file
        upload_res = client.post(
            "/api/contributor/submit-audio",
            headers={"Authorization": f"Bearer {con_token}"},
            data={
                "passageId": passage_id,
                "attribution": "SHOW_NAME",
                "durationSeconds": 60.0,
            },
            files={"file": ("real_rec_60s.wav", io.BytesIO(wav_bytes), "audio/wav")},
        )
        assert upload_res.status_code == 200
        upload_data = upload_res.json()
        recording_id = upload_data["recordingId"]
        audio_file_path = upload_data["audioFile"]

        # 6. Verify real byte size and on-disk file integrity
        # audio_file_path is filename e.g. "uuid.wav"
        filename = os.path.basename(audio_file_path)
        disk_path = os.path.join("uploads", "audio", filename)
        assert os.path.exists(disk_path), f"Audio file not found on disk at {disk_path}"
        actual_size = os.path.getsize(disk_path)
        assert actual_size == expected_size, f"Expected {expected_size} bytes, got {actual_size}"

        # 7. Reviewer logs in and retrieves pending recordings
        login_rev = client.post(
            "/api/auth/login",
            json={"identifier": "reviewer@asghi.org", "password": "ReviewerPass123!"}
        )
        assert login_rev.status_code == 200
        rev_token = login_rev.json()["accessToken"]

        pending_res = client.get(
            "/api/reviewer/pending-recordings",
            headers={"Authorization": f"Bearer {rev_token}"}
        )
        assert pending_res.status_code == 200
        pending_list = pending_res.json()
        found_pending = [r for r in pending_list if r["recordingId"] == recording_id]
        assert len(found_pending) == 1
        rec_pending = found_pending[0]
        assert rec_pending["durationSeconds"] == 60.0

        # 8. Stream audio from server as reviewer
        audio_stream_res = client.get(f"/api/audio/{filename}")
        assert audio_stream_res.status_code == 200
        assert len(audio_stream_res.content) == expected_size
        assert audio_stream_res.content[:4] == b"RIFF"

        # 9. Reviewer claims assignment and submits ACCEPT decision
        as_res = client.post(
            "/api/reviewer/assignments",
            headers={"Authorization": f"Bearer {rev_token}"},
            json={"contentId": recording_id}
        )
        assert as_res.status_code == 200
        assignment_id = as_res.json()["assignmentId"]

        verdict_res = client.post(
            "/api/reviewer/decision",
            headers={"Authorization": f"Bearer {rev_token}"},
            json={
                "assignmentId": assignment_id,
                "isApproved": True,
                "reason": "قراءة فصيحة ومتقنة تماماً",
                "isFusha": True,
                "dialectFree": True,
                "audioQuality": 5,
            }
        )
        assert verdict_res.status_code == 200

        # 10. Learner queries catalogue and verifies playable verified audio
        login_lrn = client.post(
            "/api/auth/login",
            json={"identifier": "learner@asghi.org", "password": "LearnerPass123!"}
        )
        assert login_lrn.status_code == 200
        lrn_token = login_lrn.json()["accessToken"]

        catalogue_res = client.get(
            "/api/passages",
            headers={"Authorization": f"Bearer {lrn_token}"}
        )
        assert catalogue_res.status_code == 200
        verified_passages = catalogue_res.json()
        matching = [p for p in verified_passages if p["passageId"] == passage_id]
        assert len(matching) == 1
        v_passage = matching[0]
        assert len(v_passage["audioRecordings"]) >= 1
        assert any(r["recordingId"] == recording_id and r["status"] == "VERIFIED" for r in v_passage["audioRecordings"])

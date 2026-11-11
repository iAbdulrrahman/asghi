"""Live E2E integration test against a running FastAPI backend.
Spawns a clean server process, seeds database, and executes all 5 domain flows.
"""
import io
import os
import sys
import time
import socket
import struct
import subprocess
import pytest
import httpx

from asghi.seed import seed_database


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def generate_wav_bytes(duration_seconds: int = 60, sample_rate: int = 44100) -> bytes:
    """Generate a standard 16-bit mono PCM WAV file byte stream."""
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
    block_align = num_channels * (bits_per_sample // 8)
    data_size = sample_rate * duration_seconds * (bits_per_sample // 8)

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
    pcm_data = b"\x00" * data_size
    return header + pcm_data


class LiveServer:
    def __init__(self, db_path: str, port: int):
        self.db_path = db_path
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self.process = None

    def start(self):
        env = os.environ.copy()
        env["ASGHI_DB_PATH"] = self.db_path
        env["PYTHONUNBUFFERED"] = "1"
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "asghi.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(self.port),
            "--log-level",
            "warning",
        ]
        self.process = subprocess.Popen(cmd, env=env)

    def wait_for_ready(self, timeout: float = 15.0):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.process.poll() is not None:
                raise RuntimeError(f"Server process terminated prematurely with exit code {self.process.returncode}")
            try:
                resp = httpx.get(f"{self.base_url}/healthz", timeout=1.0)
                if resp.status_code == 200:
                    return
            except httpx.RequestError:
                pass
            time.sleep(0.3)
        raise TimeoutError(f"Server on {self.base_url} did not become healthy within {timeout}s")

    def stop(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
            self.process = None


def test_live_server_full_e2e_all_flows(tmp_path):
    """Executes the complete end-to-end multi-role flow against a live server."""
    test_db = str(tmp_path / "live_e2e.db")
    seed_database(db_path=test_db)

    port = find_free_port()
    server = LiveServer(db_path=test_db, port=port)
    server.start()

    created_audio_files = []

    try:
        server.wait_for_ready(timeout=15.0)
        client = httpx.Client(base_url=server.base_url, timeout=10.0)

        # ---------------------------------------------------------
        # FLOW 1 & 4: Learner Registration, Auth, and Practice Session (Seq 3, 4)
        # ---------------------------------------------------------
        reg_res = client.post(
            "/api/auth/register",
            json={
                "email": "learner_live_e2e@asghi.org",
                "password": "LearnerE2EPass123!",
                "displayName": "متعلم تجريبي متكامل",
                "arabicLevel": "B1",
            },
        )
        assert reg_res.status_code in (200, 201), f"Register failed: {reg_res.text}"
        learner_token = reg_res.json().get("token") or reg_res.json().get("accessToken")
        learner_headers = {"Authorization": f"Bearer {learner_token}"}

        # Verify login
        login_res = client.post(
            "/api/auth/login",
            json={
                "identifier": "learner_live_e2e@asghi.org",
                "password": "LearnerE2EPass123!",
            },
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"

        # Complete learner profile
        prof_res = client.post(
            "/api/users/profile",
            headers=learner_headers,
            json={
                "displayName": "متعلم تجريبي متكامل",
                "level": "B1",
                "roleInterest": "LEARNER",
            },
        )
        assert prof_res.status_code == 200, f"Profile failed: {prof_res.text}"

        # Fetch catalogue of passages (Req 7.1)
        passages_res = client.get("/api/passages", headers=learner_headers)
        assert passages_res.status_code == 200
        passages = passages_res.json()
        assert len(passages) >= 1
        p1 = passages[0]
        p1_id = p1["passageId"]

        # Start listening test session (Seq 3 & Req 6.2)
        session_res = client.post(
            "/api/learner/sessions",
            headers=learner_headers,
            json={"passageId": p1_id},
        )
        assert session_res.status_code == 200
        session_data = session_res.json()
        session_id = session_data["sessionId"]
        assert "currentDifficulty" in session_data

        # Fetch next question (Req 6.3)
        q_res = client.get(f"/api/learner/sessions/{session_id}/question", headers=learner_headers)
        assert q_res.status_code == 200
        q_data = q_res.json()
        assert q_data["done"] is False
        q1_id = q_data["questionId"]
        q1_answers = q_data["answers"]
        chosen_answer = q1_answers[0] if q1_answers else "العربية"

        # Submit answer to question (Req 6.4, 6.5, 9)
        ans_res = client.post(
            f"/api/learner/sessions/{session_id}/answer",
            headers=learner_headers,
            json={
                "questionId": q1_id,
                "answer": chosen_answer,
            },
        )
        assert ans_res.status_code == 200
        ans_data = ans_res.json()
        assert "isCorrect" in ans_data
        assert "nextDifficulty" in ans_data

        # Finish session (Req 6.6)
        finish_res = client.post(
            f"/api/learner/sessions/{session_id}/finish",
            headers=learner_headers,
        )
        assert finish_res.status_code == 200
        finish_data = finish_res.json()
        assert "totalScore" in finish_data

        # Check Learner Progress (Req 6.6)
        prog_res = client.get("/api/learner/progress", headers=learner_headers)
        assert prog_res.status_code == 200
        prog_data = prog_res.json()
        assert "completedTests" in prog_data
        assert "streak" in prog_data
        assert "totalScore" in prog_data

        # ---------------------------------------------------------
        # FLOW 2: Contributor Claim Cycle with Real Audio Upload (Seq 1 & Req 4.2)
        # ---------------------------------------------------------
        con_login = client.post(
            "/api/auth/login",
            json={"identifier": "contributor@asghi.org", "password": "ContributorPass123!"},
        )
        assert con_login.status_code == 200
        con_token = con_login.json()["accessToken"]
        con_headers = {"Authorization": f"Bearer {con_token}"}

        # Get passages awaiting recording
        awaiting_res = client.get("/api/contributor/awaiting-recording", headers=con_headers)
        assert awaiting_res.status_code == 200
        awaiting = awaiting_res.json()
        assert len(awaiting) >= 1
        p_claim = awaiting[0]
        claim_id = p_claim["passageId"]

        # Claim passage
        claim_res = client.post(
            "/api/contributor/claim",
            headers=con_headers,
            json={"passageId": claim_id},
        )
        assert claim_res.status_code == 200

        # Concurrent claim should fail with 409 Conflict
        con2_claim = client.post(
            "/api/contributor/claim",
            headers=learner_headers,
            json={"passageId": claim_id},
        )
        assert con2_claim.status_code in (403, 409)

        # Generate real WAV bytes (75 seconds of audio)
        real_wav = generate_wav_bytes(duration_seconds=75)
        expected_size = len(real_wav)

        # Upload real audio file via multipart form
        upload_res = client.post(
            "/api/contributor/submit-audio",
            headers=con_headers,
            data={
                "passageId": claim_id,
                "attribution": "SHOW_NAME",
                "durationSeconds": 75.0,
            },
            files={"file": ("e2e_real_audio.wav", io.BytesIO(real_wav), "audio/wav")},
        )
        assert upload_res.status_code == 200
        upload_data = upload_res.json()
        rec_id = upload_data["recordingId"]
        rec_filename = os.path.basename(upload_data["audioFile"])
        created_audio_files.append(os.path.join("uploads", "audio", rec_filename))

        # Verify on-disk file size matches uploaded byte count exactly
        disk_audio_path = os.path.join("uploads", "audio", rec_filename)
        assert os.path.exists(disk_audio_path), f"Audio file not found on disk at {disk_audio_path}"
        assert os.path.getsize(disk_audio_path) == expected_size

        # ---------------------------------------------------------
        # FLOW 3: Reviewer Queue, Audio Streaming & Verdict (Seq 2)
        # ---------------------------------------------------------
        rev_login = client.post(
            "/api/auth/login",
            json={"identifier": "reviewer@asghi.org", "password": "ReviewerPass123!"},
        )
        assert rev_login.status_code == 200
        rev_token = rev_login.json()["accessToken"]
        rev_headers = {"Authorization": f"Bearer {rev_token}"}

        # Reviewer queue contains newly uploaded recording
        rev_queue = client.get("/api/reviewer/pending-recordings", headers=rev_headers)
        assert rev_queue.status_code == 200
        queue_items = rev_queue.json()
        matching = [item for item in queue_items if item["recordingId"] == rec_id]
        assert len(matching) == 1

        # Stream audio via GET /api/audio/{filename}
        audio_stream_res = client.get(f"/api/audio/{rec_filename}", headers=rev_headers)
        assert audio_stream_res.status_code == 200
        assert len(audio_stream_res.content) == expected_size

        # Reviewer claims assignment
        as_res = client.post(
            "/api/reviewer/assignments",
            headers=rev_headers,
            json={"contentId": rec_id},
        )
        assert as_res.status_code == 200
        assignment_id = as_res.json()["assignmentId"]

        # Reviewer submits APPROVED verdict
        verdict_res = client.post(
            "/api/reviewer/decision",
            headers=rev_headers,
            json={
                "assignmentId": assignment_id,
                "isApproved": True,
                "reason": "تسجيل صوتي فصيح ودقيق ومتقن النطق",
                "isFusha": True,
                "dialectFree": True,
                "audioQuality": 5,
            },
        )
        assert verdict_res.status_code == 200

        # Learner now sees this newly verified passage in catalogue (Req 7.1)
        updated_catalogue = client.get("/api/passages", headers=learner_headers)
        assert updated_catalogue.status_code == 200
        cat_ids = [p["passageId"] for p in updated_catalogue.json()]
        assert claim_id in cat_ids

        # ---------------------------------------------------------
        # FLOW 5: Flagging & Admin Dispute Resolution (Seq 5 & Req 5.4, 10.2)
        # ---------------------------------------------------------
        flag_res = client.post(
            "/api/learner/flag",
            headers=learner_headers,
            json={
                "contentId": p1_id,
                "reason": "تشويش بسيط في مقطع البداية",
            },
        )
        assert flag_res.status_code == 200
        flag_id = flag_res.json()["flagId"]

        # Admin logs in
        admin_login = client.post(
            "/api/auth/login",
            json={"identifier": "admin@asghi.org", "password": "AdminPass123!"},
        )
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["accessToken"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Admin lists flags
        flags_res = client.get("/api/admin/flags", headers=admin_headers)
        assert flags_res.status_code == 200
        admin_flags = flags_res.json()
        flag_entry = next((f for f in admin_flags if f["flagId"] == flag_id), None)
        assert flag_entry is not None

        # Admin resolves flag
        resolve_flag_res = client.post(
            f"/api/admin/flags/{flag_id}/resolve",
            headers=admin_headers,
            json={"newState": "ACTION_TAKEN"},
        )
        assert resolve_flag_res.status_code == 200

        # Admin resolves dispute
        resolve_dispute_res = client.post(
            f"/api/admin/disputes/{p1_id}/resolve",
            headers=admin_headers,
            json={"action": "VERIFY"},
        )
        assert resolve_dispute_res.status_code == 200

        # Admin dashboard & report
        dash_res = client.get("/api/admin/dashboard", headers=admin_headers)
        assert dash_res.status_code == 200
        assert "verifiedPassages" in dash_res.json()["report"]

        report_res = client.get("/api/admin/report", headers=admin_headers)
        assert report_res.status_code == 200
        assert "verifiedPassages" in report_res.json()

    finally:
        server.stop()
        # Clean up disk files
        for p in created_audio_files:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass

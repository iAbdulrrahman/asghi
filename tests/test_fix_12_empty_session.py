import os
import sqlite3
from datetime import timedelta
from uuid import uuid4
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.domain.audio_recording import AudioRecording
from asghi.domain.enums import ContentStatus, Level, Origin
from asghi.domain.passage import Passage
from asghi.seed import seed_database


def test_session_creation_rejected_if_no_verified_questions(tmp_path):
    test_db = str(tmp_path / "test_empty_session.db")
    seed_database(test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    with TestClient(app) as client:
        # 1. Login as learner
        login_res = client.post(
            "/api/auth/login",
            json={"identifier": "learner@asghi.org", "password": "LearnerPass123!"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Add verified passage without any questions
        p_no_q = Passage(
            passageId=uuid4(),
            text="نص فصيح بدون أسئلة لاختبار رفض إنشاء الجلسة",
            level=Level.B1,
            topic="اختبار الجلسة الفارغة",
            duration=timedelta(seconds=90),
            origin=Origin.HUMAN,
            authorId=uuid4(),
            status=ContentStatus.VERIFIED,
        )
        p_no_q.audioRecordings.append(
            AudioRecording(
                contentId=uuid4(),
                passageId=p_no_q.passageId,
                audioFile="sample.wav",
                duration=timedelta(seconds=90),
                authorId=uuid4(),
                status=ContentStatus.VERIFIED,
            )
        )
        Passage._registry.append(p_no_q)

        # 3. Learner attempts to start session on this passage
        session_res = client.post(
            "/api/learner/sessions",
            headers=headers,
            json={"passageId": str(p_no_q.passageId)}
        )
        assert session_res.status_code == 400
        assert "لا توجد أسئلة معتمدة لهذا النص" in session_res.json()["detail"]

        # 4. Verify no orphan row in SQLite
        with sqlite3.connect(test_db) as conn:
            cnt = conn.execute("SELECT count(*) FROM test_sessions WHERE passage_id = ?", (str(p_no_q.passageId),)).fetchone()[0]
            assert cnt == 0, "No test_session row should be created for questionless passage"

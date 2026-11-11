import uuid
import os
import tempfile
from datetime import timedelta
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.repository import Repository, get_repository
from asghi.domain.enums import UserRole, Level, ContentStatus, Difficulty
from asghi.domain.passage import Passage


def test_role_profiles_persisted():
    """P3 Item 12: register via API, complete profile with role, reload from DB, role-gated call still works."""
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
    try:
        repo = Repository(db_file)
        app.dependency_overrides[get_repository] = lambda: repo
        client = TestClient(app)

        # 1. Register a new user
        reg_payload = {
            "emailOrPhone": "contributor_persisted@asghi.org",
            "password": "Password123!",
        }
        r_reg = client.post("/api/auth/register", json=reg_payload)
        assert r_reg.status_code in (200, 201), r_reg.text
        initial_token = r_reg.json()["token"]

        # 2. Complete profile and select CONTRIBUTOR role
        r_prof = client.post(
            "/api/users/profile",
            json={
                "displayName": "مساهم مسجل دائم",
                "level": "C1",
                "roleInterest": "CONTRIBUTOR",
            },
            headers={"Authorization": f"Bearer {initial_token}"},
        )
        assert r_prof.status_code == 200, r_prof.text
        contributor_token = r_prof.json()["token"]
        auth_headers = {"Authorization": f"Bearer {contributor_token}"}

        # 3. Add a passage to claim
        p = Passage(
            text="نص لاختبار دوام الملفات التعريفية للأدوار بعد إعادة التحميل",
            level=Level.B1,
            topic="Culture",
            duration=timedelta(seconds=60),
            status=ContentStatus.DRAFT,
        )
        repo.save_passage(p)

        # 4. Simulate process restart: completely new Repository instance loaded from DB
        fresh_repo = Repository(db_file)
        fresh_repo.load_all_from_db()
        app.dependency_overrides[get_repository] = lambda: fresh_repo
        fresh_client = TestClient(app)

        # 5. Role-gated call (contributor claim) with token must succeed (200)
        r_claim = fresh_client.post(
            "/api/contributor/claim",
            json={"passageId": str(p.passageId)},
            headers=auth_headers,
        )
        assert r_claim.status_code == 200, r_claim.text
        claimed_p = fresh_repo.get_passage_by_id(p.passageId)
        assert claimed_p is not None
        assert claimed_p.status == ContentStatus.CLAIMED
    finally:
        app.dependency_overrides.clear()
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except Exception:
                pass


def test_login_flow():
    """P3 Item 13: register -> login -> authorised request using only the returned token."""
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
    try:
        repo = Repository(db_file)
        app.dependency_overrides[get_repository] = lambda: repo
        client = TestClient(app)

        # 1. Register
        reg_resp = client.post("/api/auth/register", json={
            "emailOrPhone": "real_learner@asghi.org",
            "password": "LearnerPassword2026!",
        })
        assert reg_resp.status_code in (200, 201), reg_resp.text

        # 2. Login using email or phone
        login_resp = client.post("/api/auth/login", json={
            "identifier": "real_learner@asghi.org",
            "password": "LearnerPassword2026!",
        })
        assert login_resp.status_code == 200, login_resp.text
        token = login_resp.json()["token"]

        # 3. Authorised request using ONLY returned token
        auth_headers = {"Authorization": f"Bearer {token}"}
        me_resp = client.get("/api/users/me", headers=auth_headers)
        assert me_resp.status_code == 200, me_resp.text
        data = me_resp.json()
        assert data["email"] == "real_learner@asghi.org"
    finally:
        app.dependency_overrides.clear()
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except Exception:
                pass


def test_claim_race():
    """P3 Item 14: two concurrent claims (threads) -> exactly one 200, one 409."""
    from tests.test_fix_5_claim_race_and_ttl import test_claim_race_concurrent_threads
    test_claim_race_concurrent_threads()


def test_verdict_atomicity():
    """P3 Item 15: inject a failure mid-transaction -> no assignment, no status change."""
    from tests.test_fix_6_verdict_atomicity import test_verdict_atomicity_rollback_on_injected_failure
    test_verdict_atomicity_rollback_on_injected_failure()


def test_session_persisted():
    """P3 Item 16: full learner session -> rows in test_sessions, question_responses."""
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
    try:
        repo = Repository(db_file)
        app.dependency_overrides[get_repository] = lambda: repo
        client = TestClient(app)

        # 1. Register learner & get token
        r_reg = client.post("/api/auth/register", json={
            "emailOrPhone": "session_learner@asghi.org",
            "password": "Pass1234!",
        })
        init_token = r_reg.json()["token"]

        # Complete profile as LEARNER
        r_prof = client.post(
            "/api/users/profile",
            json={
                "displayName": "متعلم الجلسات",
                "level": "B1",
                "roleInterest": "LEARNER",
            },
            headers={"Authorization": f"Bearer {init_token}"},
        )
        assert r_prof.status_code == 200, r_prof.text
        token = r_prof.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Seed a passage with verified recording and verified question
        passage_id = uuid.uuid4()
        with repo._get_conn() as conn:
            conn.execute("""
            INSERT INTO passages (passage_id, text, level, topic, duration_seconds, status, origin)
            VALUES (?, 'نص جلسة التدريب', 'B1', 'General', 60, 'VERIFIED', 'AI');
            """, (str(passage_id),))

            conn.execute("""
            INSERT INTO audio_recordings (recording_id, passage_id, audio_file, duration_seconds, attribution, status, origin)
            VALUES (?, ?, '/audio/session.mp3', 60, 'SHOW_NAME', 'VERIFIED', 'AI');
            """, (str(uuid.uuid4()), str(passage_id)))

            q_id = str(uuid.uuid4())
            conn.execute("""
            INSERT INTO questions (question_id, passage_id, prompt_text, answers_json, correct_answer, explanation, difficulty, type, status, origin)
            VALUES (?, ?, 'ما هو موضوع الجلسة؟', '["أ","ب","ج","د"]', 'أ', 'تفسير', 'MEDIUM', 'MCQ', 'VERIFIED', 'AI');
            """, (q_id, str(passage_id)))

        repo.load_all_from_db()

        # 3. Start practice session at POST /api/learner/sessions
        start_resp = client.post(
            "/api/learner/sessions",
            json={"passageId": str(passage_id)},
            headers=headers,
        )
        assert start_resp.status_code == 200, start_resp.text
        session_id = start_resp.json()["sessionId"]

        # 4. Submit answer at POST /api/learner/sessions/{sessionId}/answer
        ans_resp = client.post(
            f"/api/learner/sessions/{session_id}/answer",
            json={
                "questionId": q_id,
                "answer": "أ",
                "responseTime": 4.5,
            },
            headers=headers,
        )
        assert ans_resp.status_code == 200, ans_resp.text
        assert ans_resp.json()["isCorrect"] is True

        # 5. Direct verification of rows in SQLite database tables
        with repo._get_conn() as conn:
            # Check test_sessions row
            sess_row = conn.execute(
                "SELECT session_id, total_score, current_difficulty FROM test_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            assert sess_row is not None, "Session row not found in test_sessions table"
            assert sess_row["total_score"] == 20

            # Check question_responses row
            resp_row = conn.execute(
                "SELECT response_id, session_id, question_id, is_correct FROM question_responses WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            assert resp_row is not None, "Response row not found in question_responses table"
            assert resp_row["session_id"] == session_id
            assert resp_row["question_id"] == q_id
            assert resp_row["is_correct"] == 1
    finally:
        app.dependency_overrides.clear()
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except Exception:
                pass

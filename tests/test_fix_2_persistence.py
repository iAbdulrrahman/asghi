"""Test for Item 2: Persist everything the model owns.
Must fail before fix is applied.
"""
import io
import os
import sqlite3
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.domain.enums import UserRole, Level, ContentStatus, Difficulty, Origin, AttributionType
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.domain.question import Question
from asghi.domain.audio_recording import AudioRecording
from asghi.domain.review_assignment import ReviewAssignment
from asghi.domain.review_feedback import ReviewFeedback
from asghi.repository import get_repository
from asghi.security import create_access_token


def test_test_sessions_and_responses_persisted_to_db():
    """Verify that learner session and individual question responses are written to SQLite."""
    client = TestClient(app)
    repo = get_repository()
    repo.clear_all_tables()
    User._registry.clear()
    Passage._registry.clear()

    # Create learner
    learner = User(email="learner_persist@asghi.org")
    learner.addRole(UserRole.LEARNER)
    repo.save_user(learner)
    token = create_access_token(learner.userId, [UserRole.LEARNER])

    # Create verified passage with question
    p = Passage(
        text="نص اختبار تخزين الجلسات والأسئلة",
        level=Level.B1,
        topic="عام",
        duration=timedelta(seconds=90),
        status=ContentStatus.VERIFIED,
    )
    q = Question(
        promptText="سؤال تخزين؟",
        answers=["نعم", "لا"],
        correctAnswer="نعم",
        explanation="توضيح",
        difficulty=Difficulty.MEDIUM,
        status=ContentStatus.VERIFIED,
        passageId=p.passageId,
    )
    p.addQuestion(q)
    repo.save_passage(p)

    # 1. Start session
    s_res = client.post(
        "/api/learner/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"passageId": str(p.passageId)}
    )
    assert s_res.status_code == 200
    s_id = s_res.json()["sessionId"]

    # 2. Submit answer
    a_res = client.post(
        f"/api/learner/sessions/{s_id}/answer",
        headers={"Authorization": f"Bearer {token}"},
        json={"questionId": str(q.questionId), "answer": "نعم"}
    )
    assert a_res.status_code == 200

    # 3. Finish session
    f_res = client.post(
        f"/api/learner/sessions/{s_id}/finish",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert f_res.status_code == 200

    # Verify directly in SQLite
    with repo._get_conn() as conn:
        s_row = conn.execute("SELECT * FROM test_sessions WHERE session_id = ?", (s_id,)).fetchone()
        assert s_row is not None, "test_sessions row was not found in SQLite"
        assert s_row["total_score"] > 0

        qr_row = conn.execute("SELECT * FROM question_responses WHERE session_id = ?", (s_id,)).fetchone()
        assert qr_row is not None, "question_responses row was not found in SQLite"
        assert qr_row["submitted_answer"] == "نعم"
        assert qr_row["is_correct"] == 1


def test_review_assignments_and_feedback_persisted_and_reloaded():
    """Verify that review assignments and feedback are fully hydrated on reload (quorum evidence)."""
    repo = get_repository()
    repo.clear_all_tables()
    User._registry.clear()
    Passage._registry.clear()

    # Create reviewer
    rev = User(email="rev_quorum@asghi.org")
    rp = rev.addRole(UserRole.REVIEWER)
    rp.isSpecialist = True
    repo.save_user(rev)

    # Create passage with recording
    p = Passage(text="نص لاختبار أدلة النصاب", level=Level.B2, topic="عام", duration=timedelta(seconds=90))
    rec = p.addAudio(audioFile="test_rec.mp3", duration=timedelta(seconds=90), authorId=None)
    repo.save_passage(p)

    # Assign review and submit decision
    assignment = rp.assignReview(rec.contentId)
    feedback = rp.createFeedback(isFusha=True, dialectFree=True, audioQuality=5, feedback="فصيح ومتقن")
    rp.submitDecision(assignment, feedback, isApproved=True, reason="معتمد")
    repo.save_passage(p)

    # Clear memory registries and reload from DB
    User._registry.clear()
    Passage._registry.clear()
    repo.load_all_from_db()

    # Re-fetch passage and recording
    loaded_p = repo.get_passage_by_id(p.passageId)
    assert loaded_p is not None
    loaded_rec = loaded_p.audioRecordings[0]
    assert loaded_rec.status == ContentStatus.VERIFIED
    # Quorum evidence check: reviews list must not be empty!
    assert len(loaded_rec.reviews) == 1, "Review assignment was lost on database reload"
    assert loaded_rec.reviews[0].feedback is not None, "Review feedback was lost on database reload"
    assert loaded_rec.reviews[0].feedback.isFusha is True

"""Tests for P1 Item 7:
- Answer: response + score + difficulty in one transaction
- Flag/moderation: flag status + content status in one transaction
- Upload: file first, then row (with cleanup if row fails)
"""
from datetime import timedelta
from uuid import uuid4
import pytest
from asghi.api import get_repository
from asghi.domain.enums import UserRole, Level, ContentStatus, Difficulty, FlagStatus
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.domain.question import Question
from asghi.domain.learner_profile import LearnerProfile


def test_answer_atomic_transaction_rollback():
    """Verify that recording an answer updates response, score, and difficulty in one transaction."""
    repo = get_repository()
    learner = User(email="learner_ans_tx@asghi.org")
    lp: LearnerProfile = learner.addRole(UserRole.LEARNER)
    repo.save_user(learner)

    p = Passage(text="نص اختبار ذرية الإجابة", level=Level.B1, topic="عام", duration=timedelta(seconds=90))
    q = Question(
        promptText="سؤال؟",
        answers=["نعم", "لا"],
        correctAnswer="نعم",
        explanation="توضيح",
        difficulty=Difficulty.MEDIUM,
        status=ContentStatus.VERIFIED,
        passageId=p.passageId,
    )
    p.addQuestion(q)
    repo.save_passage(p)

    session = lp.startSession(p.passageId)
    session.learnerId = learner.userId
    repo.save_test_session(session)

    # Initial baseline
    with repo._get_conn() as conn:
        s_row = conn.execute("SELECT total_score, current_difficulty FROM test_sessions WHERE session_id = ?;", (str(session.sessionId),)).fetchone()
        assert s_row["total_score"] == 0
        assert s_row["current_difficulty"] == "MEDIUM"

    result = session.submitAnswer(q.questionId, "نعم")
    qr = session.questionResponses[-1]

    # Injected failure mid-transaction must rollback both response and test_session score/difficulty
    with pytest.raises(RuntimeError):
        repo.record_answer_tx(session, qr, fail_injection=True)

    with repo._get_conn() as conn:
        qr_count = conn.execute("SELECT COUNT(*) FROM question_responses WHERE session_id = ?;", (str(session.sessionId),)).fetchone()[0]
        assert qr_count == 0, "No question_response row should exist after rollback"
        s_row = conn.execute("SELECT total_score, current_difficulty FROM test_sessions WHERE session_id = ?;", (str(session.sessionId),)).fetchone()
        assert s_row["total_score"] == 0, "Score should not be updated after rollback"

    # Successful transaction commits both
    success = repo.record_answer_tx(session, qr, fail_injection=False)
    assert success is True

    with repo._get_conn() as conn:
        qr_count = conn.execute("SELECT COUNT(*) FROM question_responses WHERE session_id = ?;", (str(session.sessionId),)).fetchone()[0]
        assert qr_count == 1
        s_row = conn.execute("SELECT total_score, current_difficulty FROM test_sessions WHERE session_id = ?;", (str(session.sessionId),)).fetchone()
        assert s_row["total_score"] == 20
        assert s_row["current_difficulty"] == "HARD"


def test_flag_resolution_atomic_transaction():
    """Verify that resolving a flag updates flag status and content status in one transaction."""
    repo = get_repository()
    reporter = User(email="reporter_tx@asghi.org")
    lp = reporter.addRole(UserRole.LEARNER)
    repo.save_user(reporter)

    p = Passage(text="نص بلاغ ذري", level=Level.B1, topic="عام", duration=timedelta(seconds=90), status=ContentStatus.VERIFIED)
    flag = lp.flagContent(p, "محتوى غير لائق")
    repo.save_passage(p)

    with repo._get_conn() as conn:
        f_row = conn.execute("SELECT status FROM content_flags WHERE flag_id = ?;", (str(flag.flagId),)).fetchone()
        assert f_row["status"] == "PENDING"

    # Injected failure rolls back
    with pytest.raises(RuntimeError):
        repo.resolve_flag_tx(flag.flagId, FlagStatus.ACTION_TAKEN, fail_injection=True)

    with repo._get_conn() as conn:
        f_row = conn.execute("SELECT status FROM content_flags WHERE flag_id = ?;", (str(flag.flagId),)).fetchone()
        assert f_row["status"] == "PENDING"
        p_row = conn.execute("SELECT status FROM passages WHERE passage_id = ?;", (str(p.passageId),)).fetchone()
        assert p_row["status"] == "VERIFIED"

    # Success commits both flag status and content status
    success = repo.resolve_flag_tx(flag.flagId, FlagStatus.ACTION_TAKEN, fail_injection=False)
    assert success is True

    with repo._get_conn() as conn:
        f_row = conn.execute("SELECT status FROM content_flags WHERE flag_id = ?;", (str(flag.flagId),)).fetchone()
        assert f_row["status"] == "ACTION_TAKEN"
        p_row = conn.execute("SELECT status FROM passages WHERE passage_id = ?;", (str(p.passageId),)).fetchone()
        assert p_row["status"] == "FLAGGED"

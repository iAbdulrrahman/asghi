"""AI & Review requirements tests: Req 3, 3.1, 3.2, 3.3.
"""
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.domain.enums import UserRole, Level, ContentStatus, Difficulty, Origin
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.domain.ai_engine import AIEngine
from asghi.security import create_access_token

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_registry():
    User._registry.clear()
    Passage._registry.clear()
    yield
    User._registry.clear()
    Passage._registry.clear()


def test_ai_generation_and_human_review():
    """Req 3: System generates passages and questions with AI, under human review."""
    admin = User(email="admin_ai@asghi.org")
    admin.addRole(UserRole.ADMIN)
    token = create_access_token(admin.userId, [UserRole.ADMIN])

    passage = Passage(
        text="",
        level=Level.B2,
        topic="العلوم",
        duration=timedelta(seconds=100),
    )

    res = client.post(
        "/api/admin/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"passageId": str(passage.passageId)}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["questionsCount"] == 3
    assert len(passage.text) > 0
    assert passage.origin == Origin.AI
    assert passage.status == ContentStatus.PENDING_REVIEW


def test_ai_content_generator():
    """Req 3.1: AI Content Generator produces Arabic passages and comprehension questions."""
    engine = AIEngine()
    passage = Passage(
        text="",
        level=Level.A2,
        topic="الثقافة",
        duration=timedelta(seconds=90),
    )
    text = engine.generatePassageText(passage.passageId)
    assert len(text) > 10
    questions = engine.generateQuestions(passage.passageId, 3)
    assert len(questions) == 3


def test_ai_question_generation_difficulties():
    """Req 3.2: Generate comprehension questions across easy, medium, and hard difficulty."""
    engine = AIEngine()
    passage = Passage(
        text="نص اختباري",
        level=Level.B1,
        topic="التاريخ",
        duration=timedelta(seconds=90),
    )
    questions = engine.generateQuestions(passage.passageId, 3)
    difficulties = {q.difficulty for q in questions}
    assert Difficulty.EASY in difficulties
    assert Difficulty.MEDIUM in difficulties
    assert Difficulty.HARD in difficulties


def test_ai_content_requires_human_review():
    """Req 3.3: AI-generated passages and questions always pass through human review before publication."""
    admin = User(email="admin_ai2@asghi.org")
    admin.addRole(UserRole.ADMIN)
    admin_token = create_access_token(admin.userId, [UserRole.ADMIN])

    rev = User(email="rev_ai@asghi.org")
    rev.addRole(UserRole.REVIEWER)
    rev_token = create_access_token(rev.userId, [UserRole.REVIEWER])

    passage = Passage(
        text="",
        level=Level.B1,
        topic="التكنولوجيا",
        duration=timedelta(seconds=90),
    )
    client.post(
        "/api/admin/generate",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"passageId": str(passage.passageId)}
    )

    # Questions are in PENDING_REVIEW
    for q in passage.questions:
        assert q.status == ContentStatus.PENDING_REVIEW

    # Reviewer fetches pending questions (Req 3.3 / 7.3)
    p_res = client.get("/api/reviewer/pending-questions", headers={"Authorization": f"Bearer {rev_token}"})
    assert p_res.status_code == 200
    pending_list = p_res.json()
    assert len(pending_list) >= 3

    # Reviewer approves first question
    target_q_id = pending_list[0]["questionId"]
    r_dec = client.post(
        f"/api/reviewer/questions/{target_q_id}/review",
        headers={"Authorization": f"Bearer {rev_token}"},
        json={"isApproved": True, "reason": "السؤال دقيق ومتوافق مع النص"}
    )
    assert r_dec.status_code == 200
    assert r_dec.json()["status"] == "VERIFIED"

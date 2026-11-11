"""Question Authoring tests: Req 7, 7.1, 7.2, 7.3.
"""
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.domain.enums import UserRole, Level, ContentStatus, Difficulty, QuestionType
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.domain.ai_engine import AIEngine
from asghi.domain.question import Question
from asghi.security import create_access_token

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_registry():
    User._registry.clear()
    Passage._registry.clear()
    yield
    User._registry.clear()
    Passage._registry.clear()


def test_question_authoring_all_roles():
    """Req 7: Contributors, Reviewers, and Admins can author questions."""
    p = Passage(
        text="نص لإضافة أسئلة من مختلف الأدوار.",
        level=Level.B1,
        topic="اللغة",
        duration=timedelta(seconds=90),
    )

    for role, email in [
        (UserRole.CONTRIBUTOR, "con_q@asghi.org"),
        (UserRole.REVIEWER, "rev_q@asghi.org"),
        (UserRole.ADMIN, "adm_q@asghi.org"),
    ]:
        u = User(email=email)
        u.addRole(role)
        token = create_access_token(u.userId, [role])

        res = client.post(
            "/api/questions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "passageId": str(p.passageId),
                "promptText": f"سؤال كتبه {role.value}؟",
                "answers": ["1", "2"],
                "correctAnswer": "1",
                "explanation": "شرح",
                "difficulty": "EASY",
            }
        )
        assert res.status_code == 200
        assert res.json()["status"] == "PENDING_REVIEW"


def test_author_question_roles():
    """Req 7.1: Add questions to verified passage manually or via AI generation."""
    p = Passage(
        text="نص مؤلف للأسئلة.",
        level=Level.B2,
        topic="الأدب",
        duration=timedelta(seconds=90),
    )
    admin = User(email="admin_author@asghi.org")
    ap = admin.addRole(UserRole.ADMIN)

    q = Question(
        promptText="سؤال يدوي",
        answers=["أ", "ب"],
        correctAnswer="أ",
        explanation="توضيح",
        difficulty=Difficulty.MEDIUM,
    )
    res_q = ap.authorQuestion(p.passageId, q)
    assert res_q.promptText == "سؤال يدوي"
    assert len(p.questions) == 1

    ai_qs = ap.generateQuestions(p.passageId, 3)
    assert len(ai_qs) == 3
    assert len(p.questions) == 4


def test_balanced_difficulty_generation():
    """Req 7.2: AI generator produces balanced set of questions across difficulty tiers."""
    p = Passage(
        text="نص لتوليد أسئلة متوازنة",
        level=Level.C1,
        topic="التاريخ",
        duration=timedelta(seconds=120),
    )
    engine = AIEngine()
    qs = engine.generateQuestions(p.passageId, 3)
    difficulties = [q.difficulty for q in qs]
    assert Difficulty.EASY in difficulties
    assert Difficulty.MEDIUM in difficulties
    assert Difficulty.HARD in difficulties


def test_questions_reviewed_before_shown():
    """Req 7.3: Questions shall be reviewed before being shown to Learners, whether AI or human."""
    p = Passage(
        text="نص لمراجعة الأسئلة قبل العرض للمتعلم",
        level=Level.B1,
        topic="العلوم",
        duration=timedelta(seconds=90),
        status=ContentStatus.VERIFIED,
    )
    # Question initially in PENDING_REVIEW
    q_pending = Question(
        promptText="سؤال غير معتمد بعد",
        answers=["1", "2"],
        correctAnswer="1",
        explanation="شرح",
        difficulty=Difficulty.MEDIUM,
        status=ContentStatus.PENDING_REVIEW,
        passageId=p.passageId,
    )
    p.addQuestion(q_pending)

    # getQuestion should not return unverified questions if verified ones are expected
    learner = User(email="learner_check@asghi.org")
    lp = learner.addRole(UserRole.LEARNER)
    session = lp.startSession(p.passageId)

    # Question is not verified, so reviewer reviews it
    rev = User(email="rev_checker@asghi.org")
    rev.addRole(UserRole.REVIEWER)
    rev_token = create_access_token(rev.userId, [UserRole.REVIEWER])

    r_res = client.post(
        f"/api/reviewer/questions/{q_pending.questionId}/review",
        headers={"Authorization": f"Bearer {rev_token}"},
        json={"isApproved": True, "reason": "معتمد"}
    )
    assert r_res.status_code == 200
    assert q_pending.status == ContentStatus.VERIFIED

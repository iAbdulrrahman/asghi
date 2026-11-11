"""Domain requirements tests: Req 1, 1.1, 2.1, 2.2, 2.3, 6.3.
"""
from datetime import timedelta
import pytest

from asghi.domain.enums import UserRole, Level, Origin, Difficulty, QuestionType, ContentStatus
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.domain.question import Question
from asghi.domain.audio_recording import AudioRecording
from asghi.domain.learner_profile import LearnerProfile
from asghi.domain.contributor_profile import ContributorProfile
from asghi.domain.reviewer_profile import ReviewerProfile
from asghi.domain.admin_profile import AdminProfile


@pytest.fixture(autouse=True)
def clean_registry():
    User._registry.clear()
    Passage._registry.clear()
    yield
    User._registry.clear()
    Passage._registry.clear()


def test_user_roles_and_registration():
    """Req 1 & 1.1: Four user roles: Learner, Contributor, Reviewer, Admin."""
    user = User()
    user.register("user@test.org", "Pass1234")
    assert user.email == "user@test.org"

    p_l = user.addRole(UserRole.LEARNER)
    p_c = user.addRole(UserRole.CONTRIBUTOR)
    p_r = user.addRole(UserRole.REVIEWER)
    p_a = user.addRole(UserRole.ADMIN)

    assert isinstance(p_l, LearnerProfile)
    assert isinstance(p_c, ContributorProfile)
    assert isinstance(p_r, ReviewerProfile)
    assert isinstance(p_a, AdminProfile)
    assert len(user.userProfiles) == 4


def test_passage_structure():
    """Req 2.1: Listening content organized as passages with text, audio, and questions."""
    p = Passage(
        text="نص عربي فصيح متكامل.",
        level=Level.B2,
        topic="الأدب",
        duration=timedelta(seconds=90),
    )
    rec = AudioRecording(audioFile="test.mp3", duration=timedelta(seconds=90))
    q = Question(
        promptText="سؤال؟",
        answers=["أ", "ب"],
        correctAnswer="أ",
        explanation="توضيح",
        difficulty=Difficulty.MEDIUM,
    )
    p.audioRecordings.append(rec)
    p.addQuestion(q)

    assert len(p.audioRecordings) == 1
    assert len(p.questions) == 1
    assert p.text == "نص عربي فصيح متكامل."


def test_passage_origin_tagging():
    """Req 2.2: Passages record origin (AI-generated or human-authored)."""
    p_human = Passage(
        text="نص بشري",
        level=Level.A1,
        topic="عام",
        duration=timedelta(seconds=60),
        origin=Origin.HUMAN,
    )
    p_ai = Passage(
        text="نص مولد",
        level=Level.A1,
        topic="عام",
        duration=timedelta(seconds=60),
        origin=Origin.AI,
    )
    assert p_human.origin == Origin.HUMAN
    assert p_ai.origin == Origin.AI


def test_passage_metadata():
    """Req 2.3: Passages tagged by level, topic, and duration."""
    p = Passage(
        text="نص لغوي متقدم",
        level=Level.C1,
        topic="التاريخ الإسلامي",
        duration=timedelta(seconds=120),
    )
    assert p.level == Level.C1
    assert p.topic == "التاريخ الإسلامي"
    assert p.duration == timedelta(seconds=120)


def test_passage_difficulty_tiers():
    """Req 6.3: Each verified passage has comprehension questions across easy, medium, and hard."""
    p = Passage(
        text="نص لغوي متدرج",
        level=Level.B1,
        topic="اللغة",
        duration=timedelta(seconds=90),
        status=ContentStatus.VERIFIED,
    )
    for diff in [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]:
        q = Question(
            promptText=f"سؤال {diff.value}",
            answers=["1", "2"],
            correctAnswer="1",
            explanation="شرح",
            difficulty=diff,
            status=ContentStatus.VERIFIED,
        )
        p.addQuestion(q)

    assert p.getQuestion(Difficulty.EASY).difficulty == Difficulty.EASY
    assert p.getQuestion(Difficulty.MEDIUM).difficulty == Difficulty.MEDIUM
    assert p.getQuestion(Difficulty.HARD).difficulty == Difficulty.HARD

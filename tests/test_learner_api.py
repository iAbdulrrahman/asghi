"""Learner API tests: Req 6, 6.1, 6.2, 6.4, 6.5, 6.6, 6.8, 9.
"""
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from asghi.api import app, get_repository
from asghi.domain.enums import UserRole, Level, ContentStatus, Difficulty, QuestionType
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.domain.audio_recording import AudioRecording
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


def _setup_verified_passage():
    p = Passage(
        text="نص تدريب المتعلم على الاستماع.",
        level=Level.B1,
        topic="الثقافة",
        duration=timedelta(seconds=90),
        status=ContentStatus.VERIFIED,
    )
    rec = AudioRecording(
        audioFile="sample.mp3",
        duration=timedelta(seconds=90),
        status=ContentStatus.VERIFIED,
        passageId=p.passageId,
    )
    p.audioRecordings.append(rec)

    q_easy = Question(
        promptText="سؤال سهل؟",
        answers=["نعم", "لا"],
        correctAnswer="نعم",
        explanation="توضيح السهل",
        difficulty=Difficulty.EASY,
        status=ContentStatus.VERIFIED,
        passageId=p.passageId,
    )
    q_med = Question(
        promptText="سؤال متوسط؟",
        answers=["خيار 1", "خيار 2"],
        correctAnswer="خيار 1",
        explanation="توضيح المتوسط",
        difficulty=Difficulty.MEDIUM,
        status=ContentStatus.VERIFIED,
        passageId=p.passageId,
    )
    q_hard = Question(
        promptText="سؤال صعب؟",
        answers=["أ", "ب"],
        correctAnswer="أ",
        explanation="توضيح الصعب",
        difficulty=Difficulty.HARD,
        status=ContentStatus.VERIFIED,
        passageId=p.passageId,
    )
    p.addQuestion(q_easy)
    p.addQuestion(q_med)
    p.addQuestion(q_hard)
    get_repository().save_passage(p)
    return p


def test_learner_full_practice_session():
    """Req 6: Full learner practice session from browse to finish and score update."""
    learner = User(email="learner_full@asghi.org")
    lp = learner.addRole(UserRole.LEARNER)
    token = create_access_token(learner.userId, [UserRole.LEARNER])

    p = _setup_verified_passage()

    # 1. Start session
    s_res = client.post(
        "/api/learner/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"passageId": str(p.passageId)}
    )
    assert s_res.status_code == 200
    s_id = s_res.json()["sessionId"]

    # 2. Get question
    q_res = client.get(f"/api/learner/sessions/{s_id}/question", headers={"Authorization": f"Bearer {token}"})
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["done"] is False

    # 3. Answer question
    a_res = client.post(
        f"/api/learner/sessions/{s_id}/answer",
        headers={"Authorization": f"Bearer {token}"},
        json={"questionId": q_data["questionId"], "answer": "خيار 1"}
    )
    assert a_res.status_code == 200
    assert a_res.json()["isCorrect"] is True

    # 4. Finish session
    f_res = client.post(f"/api/learner/sessions/{s_id}/finish", headers={"Authorization": f"Bearer {token}"})
    assert f_res.status_code == 200
    assert lp.progress.totalScore > 0


def test_browse_and_play_verified_audio():
    """Req 6.1: Browse and play verified Fusha audio by level, topic, length."""
    learner = User(email="learner_play@asghi.org")
    learner.addRole(UserRole.LEARNER)
    token = create_access_token(learner.userId, [UserRole.LEARNER])

    p = _setup_verified_passage()

    # Browse
    b_res = client.get("/api/passages?level=B1&topic=الثقافة")
    assert b_res.status_code == 200
    items = b_res.json()
    assert len(items) >= 1
    assert items[0]["verifiedAudioCount"] >= 1

    # Play audio with speed 1.25x
    p_res = client.post(
        "/api/learner/play",
        headers={"Authorization": f"Bearer {token}"},
        json={"passageId": str(p.passageId), "playbackSpeed": 1.25}
    )
    assert p_res.status_code == 200
    assert p_res.json()["playbackSpeed"] == 1.25


def test_start_and_run_listening_test():
    """Req 6.2: Learner can take a listening test on any passage."""
    learner = User(email="learner_test@asghi.org")
    learner.addRole(UserRole.LEARNER)
    token = create_access_token(learner.userId, [UserRole.LEARNER])

    p = _setup_verified_passage()

    res = client.post(
        "/api/learner/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"passageId": str(p.passageId)}
    )
    assert res.status_code == 200
    assert "sessionId" in res.json()


def test_adaptive_difficulty_progression():
    """Req 6.4: The app adapts question difficulty to the Learner's performance."""
    learner = User(email="learner_adapt@asghi.org")
    learner.addRole(UserRole.LEARNER)
    token = create_access_token(learner.userId, [UserRole.LEARNER])

    p = _setup_verified_passage()
    s_res = client.post(
        "/api/learner/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"passageId": str(p.passageId)}
    )
    s_id = s_res.json()["sessionId"]

    # Session starts at MEDIUM
    q1_res = client.get(f"/api/learner/sessions/{s_id}/question", headers={"Authorization": f"Bearer {token}"})
    assert q1_res.json()["difficulty"] == "MEDIUM"

    # Submit correct answer -> adapts up to HARD
    ans_res = client.post(
        f"/api/learner/sessions/{s_id}/answer",
        headers={"Authorization": f"Bearer {token}"},
        json={"questionId": q1_res.json()["questionId"], "answer": "خيار 1"}
    )
    assert ans_res.json()["isCorrect"] is True
    assert ans_res.json()["nextDifficulty"] == "HARD"

    # Next question should be HARD
    q2_res = client.get(f"/api/learner/sessions/{s_id}/question", headers={"Authorization": f"Bearer {token}"})
    assert q2_res.json()["difficulty"] == "HARD"

    # Submit incorrect answer -> adapts down to MEDIUM
    ans2_res = client.post(
        f"/api/learner/sessions/{s_id}/answer",
        headers={"Authorization": f"Bearer {token}"},
        json={"questionId": q2_res.json()["questionId"], "answer": "إجابة خاطئة"}
    )
    assert ans2_res.json()["isCorrect"] is False
    assert ans2_res.json()["nextDifficulty"] == "MEDIUM"


def test_score_responses_and_explanations():
    """Req 6.5: App scores responses and shows correct answers with explanations."""
    learner = User(email="learner_score@asghi.org")
    learner.addRole(UserRole.LEARNER)
    token = create_access_token(learner.userId, [UserRole.LEARNER])

    p = _setup_verified_passage()
    s_res = client.post(
        "/api/learner/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"passageId": str(p.passageId)}
    )
    s_id = s_res.json()["sessionId"]

    q_res = client.get(f"/api/learner/sessions/{s_id}/question", headers={"Authorization": f"Bearer {token}"})
    q_id = q_res.json()["questionId"]

    ans_res = client.post(
        f"/api/learner/sessions/{s_id}/answer",
        headers={"Authorization": f"Bearer {token}"},
        json={"questionId": q_id, "answer": "خيار 1"}
    )
    data = ans_res.json()
    assert data["totalScore"] == 20
    assert "توضيح" in data["explanation"]


def test_learner_progress_tracking():
    """Req 6.6: App tracks Learner progress over time."""
    learner = User(email="learner_prog@asghi.org")
    lp = learner.addRole(UserRole.LEARNER)
    token = create_access_token(learner.userId, [UserRole.LEARNER])

    lp.progress.update(totalScore=150, timeSpent=300)

    res = client.get("/api/learner/progress", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["totalScore"] == 150
    assert res.json()["totalTimeSpent"] == 300


def test_actionable_feedback_on_wrong_answer():
    """Req 9: App gives Learners actionable feedback on wrong answers."""
    learner = User(email="learner_fb@asghi.org")
    learner.addRole(UserRole.LEARNER)
    token = create_access_token(learner.userId, [UserRole.LEARNER])

    p = _setup_verified_passage()
    s_res = client.post(
        "/api/learner/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"passageId": str(p.passageId)}
    )
    s_id = s_res.json()["sessionId"]

    q_res = client.get(f"/api/learner/sessions/{s_id}/question", headers={"Authorization": f"Bearer {token}"})
    q_id = q_res.json()["questionId"]

    # Submit wrong answer
    ans_res = client.post(
        f"/api/learner/sessions/{s_id}/answer",
        headers={"Authorization": f"Bearer {token}"},
        json={"questionId": q_id, "answer": "إجابة غير صحيحة"}
    )
    data = ans_res.json()
    assert data["isCorrect"] is False
    assert data["correctAnswer"] == "خيار 1"
    assert len(data["explanation"]) > 0


def test_offline_package_endpoint():
    """Req 6.8: Offline package download manifest (Req 6.8 marked out-of-scope for sync, manifest supported)."""
    p = _setup_verified_passage()
    learner = User(email=f"offline_{p.passageId.hex[:6]}@asghi.org")
    learner.addRole(UserRole.LEARNER)
    token = create_access_token(learner.userId, [UserRole.LEARNER])

    # anonymous callers must not reach the manifest at all
    assert client.get(f"/api/passages/{p.passageId}/offline-package").status_code in (401, 403)

    res = client.get(
        f"/api/passages/{p.passageId}/offline-package",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["passageId"] == str(p.passageId)
    assert len(data["audio"]) >= 1
    assert len(data["questions"]) >= 1
    # the answer key is not part of a downloadable package
    assert all("correctAnswer" not in q and "explanation" not in q for q in data["questions"])

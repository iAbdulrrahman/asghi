"""Reviewer API tests: Req 5, 5.1, 5.2, 5.3, 5.4, 5.5.
"""
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.domain.enums import UserRole, Level, ContentStatus
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.domain.audio_recording import AudioRecording
from asghi.security import create_access_token

from asghi.domain.reviewable_content import ReviewableContent

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_registry():
    User._registry.clear()
    Passage._registry.clear()
    ReviewableContent._registry.clear()
    yield
    User._registry.clear()
    Passage._registry.clear()
    ReviewableContent._registry.clear()



def test_reviewer_verification_flow():
    """Req 5: Complete review and verification flow."""
    rev = User(email="rev_spec@asghi.org")
    rp = rev.addRole(UserRole.REVIEWER)
    rp.isSpecialist = True
    token = create_access_token(rev.userId, [UserRole.REVIEWER])

    p = Passage(
        text="نص لمراجعة الصوت",
        level=Level.B1,
        topic="الثقافة",
        duration=timedelta(seconds=90),
    )
    rec = AudioRecording(audioFile="test.mp3", duration=timedelta(seconds=90), passageId=p.passageId)
    p.audioRecordings.append(rec)

    # 1. Assign review
    as_res = client.post(
        "/api/reviewer/assignments",
        headers={"Authorization": f"Bearer {token}"},
        json={"contentId": str(rec.contentId)}
    )
    assert as_res.status_code == 200
    assignment_id = as_res.json()["assignmentId"]

    # 2. Submit decision
    dec_res = client.post(
        "/api/reviewer/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "assignmentId": assignment_id,
            "isFusha": True,
            "dialectFree": True,
            "audioQuality": 5,
            "isApproved": True,
            "reason": "تسجيل سليم وفصيح"
        }
    )
    assert dec_res.status_code == 200
    assert rec.status == ContentStatus.VERIFIED


def test_reviewer_evaluation():
    """Req 5.1: Reviewer can listen to pending recording and evaluate against defined criteria."""
    rev = User(email="rev_eval@asghi.org")
    rev.addRole(UserRole.REVIEWER)
    token = create_access_token(rev.userId, [UserRole.REVIEWER])

    p = Passage(
        text="نص لتقييم المراجع",
        level=Level.A2,
        topic="العلوم",
        duration=timedelta(seconds=80),
    )
    rec = AudioRecording(audioFile="eval.mp3", duration=timedelta(seconds=80), passageId=p.passageId)
    p.audioRecordings.append(rec)

    # List pending
    list_res = client.get("/api/reviewer/pending-recordings", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    assert any(r["recordingId"] == str(rec.contentId) for r in list_res.json())


def test_specialist_vs_general_reviewers_threshold():
    """Req 5.2: Recording requires either 1 specialist reviewer or 3 independent general reviewers."""
    # 1. Specialist test
    rec_spec = AudioRecording(audioFile="spec.mp3", duration=timedelta(seconds=70))
    rev_spec = User(email="spec_user@asghi.org")
    sp = rev_spec.addRole(UserRole.REVIEWER)
    sp.isSpecialist = True
    as_spec = sp.assignReview(rec_spec.contentId)
    sp.submitDecision(as_spec, sp.createFeedback(True, True), isApproved=True)
    assert rec_spec.meetsThreshold() is True
    assert rec_spec.status == ContentStatus.VERIFIED

    # 2. General reviewers test: 1 is not enough, 2 is not enough, 3 is enough
    rec_gen = AudioRecording(audioFile="gen.mp3", duration=timedelta(seconds=70))
    for i in range(2):
        u = User(email=f"gen{i}@asghi.org")
        gp = u.addRole(UserRole.REVIEWER)
        as_g = gp.assignReview(rec_gen.contentId)
        gp.submitDecision(as_g, gp.createFeedback(True, True), isApproved=True)
        assert rec_gen.meetsThreshold() is False

    # 3rd general reviewer approves
    u3 = User(email="gen3@asghi.org")
    gp3 = u3.addRole(UserRole.REVIEWER)
    as_g3 = gp3.assignReview(rec_gen.contentId)
    gp3.submitDecision(as_g3, gp3.createFeedback(True, True), isApproved=True)
    assert rec_gen.meetsThreshold() is True
    assert rec_gen.status == ContentStatus.VERIFIED


def test_prevent_author_self_review():
    """Req 5.3 & Seq 2 break branch: Prevent user from reviewing their own recording."""
    user = User(email="author_reviewer@asghi.org")
    cp = user.addRole(UserRole.CONTRIBUTOR)
    rp = user.addRole(UserRole.REVIEWER)
    token = create_access_token(user.userId, [UserRole.REVIEWER])

    p = Passage(
        text="نص لمنع المراجعة الذاتية",
        level=Level.B2,
        topic="التاريخ",
        duration=timedelta(seconds=80),
    )
    rec = AudioRecording(
        audioFile="self.mp3",
        duration=timedelta(seconds=80),
        authorId=rp.userRoleProfileId,
        passageId=p.passageId,
    )
    p.audioRecordings.append(rec)

    res = client.post(
        "/api/reviewer/assignments",
        headers={"Authorization": f"Bearer {token}"},
        json={"contentId": str(rec.contentId)}
    )
    assert res.status_code == 400
    assert "cannot review their own submission" in res.json()["detail"]


def test_dispute_resolution_policy():
    """Req 5.4 & Seq 2: Handle reviewer disagreements with defined dispute policy (Admin resolveDispute)."""
    admin = User(email="admin_disp@asghi.org")
    admin.addRole(UserRole.ADMIN)
    token = create_access_token(admin.userId, [UserRole.ADMIN])

    p = Passage(
        text="نص متنازع عليه بين المراجعين",
        level=Level.C1,
        topic="الفلسفة",
        duration=timedelta(seconds=100),
    )
    rec = AudioRecording(audioFile="disp.mp3", duration=timedelta(seconds=100), passageId=p.passageId)
    p.audioRecordings.append(rec)

    # Admin resolves dispute to VERIFIED
    res = client.post(
        f"/api/admin/disputes/{rec.contentId}/resolve",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "VERIFY"}
    )
    assert res.status_code == 200
    assert rec.status == ContentStatus.VERIFIED


def test_fusha_and_dialect_free_verification():
    """Req 5.5: Reviewers shall explicitly verify recording is in Fusha and free of dialectal pronunciation."""
    rev = User(email="rev_dial@asghi.org")
    rp = rev.addRole(UserRole.REVIEWER)
    rp.isSpecialist = True
    token = create_access_token(rev.userId, [UserRole.REVIEWER])

    p = Passage(
        text="نص لاختبار اللهجات",
        level=Level.B1,
        topic="اللغة",
        duration=timedelta(seconds=90),
    )
    rec = AudioRecording(audioFile="dialect.mp3", duration=timedelta(seconds=90), passageId=p.passageId)
    p.audioRecordings.append(rec)

    as_res = client.post(
        "/api/reviewer/assignments",
        headers={"Authorization": f"Bearer {token}"},
        json={"contentId": str(rec.contentId)}
    )
    assignment_id = as_res.json()["assignmentId"]

    # Decision with dialectFree=False (should reject despite isApproved=True)
    dec_res = client.post(
        "/api/reviewer/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "assignmentId": assignment_id,
            "isFusha": True,
            "dialectFree": False,
            "audioQuality": 4,
            "isApproved": True,
            "reason": ""
        }
    )
    assert dec_res.status_code == 200
    assert rec.status == ContentStatus.REJECTED
    assert "Fusha" in rec.rejectionReason or "dialect" in rec.rejectionReason

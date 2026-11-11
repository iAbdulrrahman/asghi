"""Contributor API tests: Req 4, 4.1, 4.2, 4.3, 4.4, 8.
"""
from datetime import timedelta
import io
import pytest
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.domain.enums import UserRole, Level, ContentStatus, AttributionType
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.domain.contributor_profile import ContributorProfile
from asghi.domain.audio_recording import AudioRecording
from asghi.security import create_access_token

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_registry():
    User._registry.clear()
    Passage._registry.clear()
    yield
    User._registry.clear()
    Passage._registry.clear()


def test_contributor_recording_cycle():
    """Req 4: Contributor full recording submission cycle."""
    con = User(email="con_full@asghi.org")
    con.addRole(UserRole.CONTRIBUTOR)
    token = create_access_token(con.userId, [UserRole.CONTRIBUTOR])

    p = Passage(
        text="نص متكامل لتجربة دورة المساهم.",
        level=Level.B1,
        topic="الثقافة",
        duration=timedelta(seconds=90),
    )

    # 1. Claim
    c_res = client.post(
        "/api/contributor/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={"passageId": str(p.passageId)}
    )
    assert c_res.status_code == 200

    # 2. Upload audio
    audio_content = b"\xff\xfb\x90\x64" * 100
    u_res = client.post(
        "/api/contributor/submit-audio",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "passageId": str(p.passageId),
            "attribution": "SHOW_NAME",
            "durationSeconds": 90.0,
        },
        files={"file": ("test_full.mp3", io.BytesIO(audio_content), "audio/mpeg")}
    )
    assert u_res.status_code == 200
    assert u_res.json()["status"] == "PENDING_REVIEW"


def test_browse_and_claim_passages():
    """Req 4.1: Browse passages needing recording and claim one."""
    con = User(email="con_claim@asghi.org")
    con.addRole(UserRole.CONTRIBUTOR)
    token = create_access_token(con.userId, [UserRole.CONTRIBUTOR])

    p1 = Passage(
        text="نص ينتظر التسجيل 1",
        level=Level.A2,
        topic="العلوم",
        duration=timedelta(seconds=60),
    )

    res = client.get("/api/contributor/awaiting-recording", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    items = res.json()
    assert any(item["passageId"] == str(p1.passageId) for item in items)

    # Claim p1
    c_res = client.post(
        "/api/contributor/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={"passageId": str(p1.passageId)}
    )
    assert c_res.status_code == 200
    assert p1.claimedBy is not None


def test_upload_audio_recording():
    """Req 4.2: Upload an existing audio file or in-app recording."""
    con = User(email="con_up@asghi.org")
    con.addRole(UserRole.CONTRIBUTOR)
    token = create_access_token(con.userId, [UserRole.CONTRIBUTOR])

    p = Passage(
        text="نص لرفع الصوت",
        level=Level.B2,
        topic="التاريخ",
        duration=timedelta(seconds=90),
    )
    p.claim(con.userProfiles[0].userRoleProfileId)

    audio_bytes = b"\xff\xfb\x90\x64" * 50
    res = client.post(
        "/api/contributor/submit-audio",
        headers={"Authorization": f"Bearer {token}"},
        data={"passageId": str(p.passageId), "attribution": "SHOW_NAME", "durationSeconds": 85.0},
        files={"file": ("speech.mp3", io.BytesIO(audio_bytes), "audio/mpeg")}
    )
    assert res.status_code == 200
    assert len(p.audioRecordings) == 1


def test_passage_display_and_tashkeel_toggle():
    """Req 4.3: App shows passage text alongside recorder with optional tashkeel display."""
    p = Passage(
        text="كَتَبَ الطَّالِبُ الدَّرْسَ بِعِنَايَةٍ.",
        level=Level.A1,
        topic="القواعد",
        duration=timedelta(seconds=60),
    )
    # Fetch with Tashkeel
    r1 = client.get(f"/api/passages/{p.passageId}/text?withTashkeel=true")
    assert r1.status_code == 200
    assert "َ" in r1.json()["text"]

    # Fetch without Tashkeel
    r2 = client.get(f"/api/passages/{p.passageId}/text?withTashkeel=false")
    assert r2.status_code == 200
    assert "َ" not in r2.json()["text"]
    assert "كتب الطالب الدرس بعناية" in r2.json()["text"]


def test_attribution_choice():
    """Req 4.4: Contributor can choose whether their name is shown publicly (SHOW_NAME vs ANONYMOUS)."""
    con = User(email="con_attr@asghi.org")
    con.addRole(UserRole.CONTRIBUTOR)
    token = create_access_token(con.userId, [UserRole.CONTRIBUTOR])

    p = Passage(
        text="نص لاختبار خيار النسبة",
        level=Level.B1,
        topic="الأدب",
        duration=timedelta(seconds=70),
    )
    p.claim(con.userProfiles[0].userRoleProfileId)

    audio_bytes = b"\xff\xfb\x90\x64" * 50
    res = client.post(
        "/api/contributor/submit-audio",
        headers={"Authorization": f"Bearer {token}"},
        data={"passageId": str(p.passageId), "attribution": "ANONYMOUS", "durationSeconds": 70.0},
        files={"file": ("anon.mp3", io.BytesIO(audio_bytes), "audio/mpeg")}
    )
    assert res.status_code == 200
    assert res.json()["attribution"] == "ANONYMOUS"


def test_rejection_explanation_visible_to_contributor():
    """Req 8: The app shall explain to Contributors why a submission was rejected."""
    con = User(email="con_rej@asghi.org")
    cp = con.addRole(UserRole.CONTRIBUTOR)
    token = create_access_token(con.userId, [UserRole.CONTRIBUTOR])

    p = Passage(
        text="نص يحتوي على تسجيل مرفوض",
        level=Level.B2,
        topic="عام",
        duration=timedelta(seconds=80),
    )
    rec = AudioRecording(
        audioFile="bad_rec.mp3",
        duration=timedelta(seconds=80),
        authorId=cp.userRoleProfileId,
        passageId=p.passageId,
        status=ContentStatus.REJECTED,
    )
    rec.reject("التسجيل غير واضح وتوجد ضوضاء بيئية مرتفعة")
    p.audioRecordings.append(rec)

    res = client.get("/api/contributor/submissions", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    submissions = res.json()
    assert len(submissions) >= 1
    rejected = [s for s in submissions if s["recordingId"] == str(rec.contentId)][0]
    assert rejected["status"] == "REJECTED"
    assert "ضوضاء" in rejected["rejectionReason"]

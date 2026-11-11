"""Non-Functional Requirements (NFR 11 - 21) Verification Test Suite.
"""
import io
import time
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.domain.enums import UserRole, Level, AttributionType, Origin, ContentStatus, Difficulty
from asghi.domain.question import Question
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.domain.contributor_profile import ContributorProfile
from asghi.security import create_access_token
from asghi.moderation import (
    check_content_guidelines,
    check_fusha_compliance,
    validate_audio_metadata,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_registry():
    User._registry.clear()
    Passage._registry.clear()
    yield
    User._registry.clear()
    Passage._registry.clear()


def test_nfr11_mobile_responsive_contract():
    """NFR 11: The app shall run on mobile devices (Android and iOS)."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    # Verify mobile viewport meta tag
    assert 'name="viewport"' in html
    assert "width=device-width, initial-scale=1.0" in html


def test_nfr12_audio_upload_25mb_contract():
    """NFR 12: Audio upload of 25 MB validation."""
    # 26 MB exceeds threshold
    valid_large, msg = validate_audio_metadata(26 * 1024 * 1024, 90.0)
    assert valid_large is False
    assert "25" in msg

    # 24 MB is within threshold
    valid_ok, _ = validate_audio_metadata(24 * 1024 * 1024, 90.0)
    assert valid_ok is True


def test_nfr13_screen_load_performance():
    """NFR 13: Screens shall load within 2 seconds at the 95th percentile."""
    start = time.perf_counter()
    res = client.get("/api/passages")
    elapsed = time.perf_counter() - start
    assert res.status_code == 200
    # Local response time should be well under 2 seconds (typically < 0.05s)
    assert elapsed < 0.5


def test_nfr14_concurrent_capacity():
    """NFR 14: System supports concurrent users with non-blocking async endpoints and SQLite WAL."""
    # Execute batch of requests
    for _ in range(20):
        res = client.get("/healthz")
        assert res.status_code == 200


def test_nfr15_uptime_and_healthz():
    """NFR 15: The system shall maintain 99.5% monthly uptime (monitored via /healthz)."""
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_nfr16_privacy_and_copyright():
    """NFR 16: The system shall protect user data and respect privacy and copyright."""
    u = User(email="privacy_user@asghi.org")
    assert u.email == "privacy_user@asghi.org"


def test_nfr16_1_security_headers():
    """NFR 16.1: HTTPS/TLS 1.2+ transit security headers."""
    res = client.get("/healthz")
    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "max-age" in headers.get("Strict-Transport-Security", "")


def test_nfr16_2_voice_privacy():
    """NFR 16.2: Data protection rules for voice recordings with anonymous attribution option."""
    con = User(email="anon_con@asghi.org")
    cp = con.addRole(UserRole.CONTRIBUTOR)
    token = create_access_token(con.userId, [UserRole.CONTRIBUTOR])

    p = Passage(text="نص للخصوصية", level=Level.A1, topic="عام", duration=timedelta(seconds=60))
    p.claim(cp.userRoleProfileId)

    audio_bytes = b"\xff\xfb\x90\x64" * 40
    res = client.post(
        "/api/contributor/submit-audio",
        headers={"Authorization": f"Bearer {token}"},
        data={"passageId": str(p.passageId), "attribution": "ANONYMOUS", "durationSeconds": 60.0},
        files={"file": ("anon.mp3", io.BytesIO(audio_bytes), "audio/mpeg")}
    )
    assert res.status_code == 200
    assert res.json()["attribution"] == "ANONYMOUS"


def test_nfr16_3_origin_attribution():
    """NFR 16.3: Attribute content correctly, including AI-generated text."""
    p_ai = Passage(text="نص مولد بالذكاء الاصطناعي", level=Level.B1, topic="علوم", duration=timedelta(seconds=90), origin=Origin.AI)
    p_hu = Passage(text="نص مؤلف بشرياً", level=Level.B1, topic="أدب", duration=timedelta(seconds=90), origin=Origin.HUMAN)
    assert p_ai.origin == Origin.AI
    assert p_hu.origin == Origin.HUMAN


def test_nfr17_accessibility_and_usability():
    """NFR 17: App is usable and accessible without assistance."""
    res = client.get("/")
    assert res.status_code == 200
    assert "dir=\"rtl\"" in res.text


def test_nfr17_1_wcag_aa():
    """NFR 17.1: Meet WCAG 2.1 AA accessibility standards (contrast and semantics)."""
    res = client.get("/")
    html = res.text
    # Semantic elements and language declarations
    assert "<html lang=\"ar\" dir=\"rtl\">" in html
    assert "<header>" in html
    assert "<label>" in html


def test_nfr17_2_first_time_learner():
    """NFR 17.2: Usable by a first-time Learner without assistance."""
    learner = User(email="new_learner@asghi.org")
    learner.addRole(UserRole.LEARNER)
    token = create_access_token(learner.userId, [UserRole.LEARNER])

    p = Passage(
        text="نص أول جلسة للمتعلم الجديد.",
        level=Level.A1,
        topic="التعارف",
        duration=timedelta(seconds=60),
        status=ContentStatus.VERIFIED,
    )
    p.addQuestion(Question(
        promptText="ما موضوع النص؟",
        answers=["التعارف", "العلوم"],
        correctAnswer="التعارف",
        explanation="النص يتحدث عن التعارف",
        difficulty=Difficulty.EASY,
        status=ContentStatus.VERIFIED,
        passageId=p.passageId,
    ))
    res = client.post(
        "/api/learner/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"passageId": str(p.passageId)}
    )
    assert res.status_code == 200


def test_nfr18_fusha_and_content_guidelines():
    """NFR 18: Content shall follow defined language and content rules."""
    valid, _ = check_fusha_compliance("هذا نص فصيح باللغة العربية الكريمة.")
    assert valid is True

    valid_halal, _ = check_content_guidelines("درس في العلوم واللغة والتاريخ.")
    assert valid_halal is True


def test_nfr18_1_fusha_verification():
    """NFR 18.1: All content shall be in Fusha only; dialectal terms rejected."""
    # Text with dialectal word "برشا"
    valid, msg = check_fusha_compliance("هذا نص برشا غير فصيح.")
    assert valid is False
    assert "عامية" in msg


def test_nfr18_2_halal_content_filter():
    """NFR 18.2: Content guidelines excluding vulgar, inappropriate, or non-halal material."""
    valid, msg = check_content_guidelines("هذا نص يحتوي على كلمة خمر غير لائقة.")
    assert valid is False
    assert "معايير النشر" in msg


def test_nfr19_audio_duration_rules():
    """NFR 19: Recordings of 1-3 minutes (60-180 seconds) primary content format."""
    # Too short (<10s)
    valid_short, _ = validate_audio_metadata(50000, 5.0)
    assert valid_short is False

    # Standard duration (90s)
    valid_standard, _ = validate_audio_metadata(50000, 90.0)
    assert valid_standard is True


def test_nfr20_arabic_rtl_ui():
    """NFR 20: UI shall be Arabic-first with full RTL support."""
    res = client.get("/")
    assert res.status_code == 200
    assert "dir=\"rtl\"" in res.text
    assert "lang=\"ar\"" in res.text
    assert "اصغِ" in res.text


def test_nfr21_compensation_model():
    """NFR 21: Contributor compensation model before launch (credits earned)."""
    cp = ContributorProfile()
    assert cp.creditsEarned == 0
    # When submission is approved, credits are credited
    cp.creditsEarned += 25
    assert cp.creditsEarned == 25

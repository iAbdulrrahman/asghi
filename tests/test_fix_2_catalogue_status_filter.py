"""Failing test for P0 Item 2:
Passage.browse() and GET /api/passages must filter to VERIFIED passages
that have at least one VERIFIED audio recording (unless include_all=True).
Flagged passages must disappear after resolveFlag with ACTION_TAKEN.
"""
from uuid import uuid4
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from asghi.domain.passage import Passage
from asghi.domain.audio_recording import AudioRecording
from asghi.domain.enums import Level, Origin, ContentStatus, FlagStatus
from asghi.domain.content_flag import ContentFlag
from asghi.domain.user import User
from asghi.domain.admin_profile import AdminProfile
from asghi.api import app, get_repository
from asghi.seed import seed_database
import os

def test_browse_filters_unverified_and_requires_verified_audio(tmp_path):
    test_db = str(tmp_path / "test_catalogue_filter.db")
    seed_database(test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    # Clear memory registry to build clean controlled set
    Passage._registry.clear()

    # 1. DRAFT passage
    p_draft = Passage(
        passageId=uuid4(), text="مسودة نص غير مكتمل",
        level=Level.A1, topic="مسودة", duration=timedelta(seconds=60),
        origin=Origin.HUMAN, authorId=uuid4(), status=ContentStatus.DRAFT
    )
    Passage._registry.append(p_draft)

    # 2. CLAIMED passage
    p_claimed = Passage(
        passageId=uuid4(), text="نص محجوز للتسجيل",
        level=Level.A2, topic="حجز", duration=timedelta(seconds=70),
        origin=Origin.HUMAN, authorId=uuid4(), status=ContentStatus.CLAIMED,
        claimedBy=uuid4()
    )
    Passage._registry.append(p_claimed)

    # 3. PENDING_REVIEW passage
    p_pending = Passage(
        passageId=uuid4(), text="نص قيد مراجعة التسجيل",
        level=Level.B1, topic="مراجعة", duration=timedelta(seconds=80),
        origin=Origin.HUMAN, authorId=uuid4(), status=ContentStatus.PENDING_REVIEW
    )
    Passage._registry.append(p_pending)

    # 4. VERIFIED passage WITHOUT verified audio (only pending recording)
    p_no_audio = Passage(
        passageId=uuid4(), text="نص معتمد بدون صوت معتمد",
        level=Level.B2, topic="بدون صوت", duration=timedelta(seconds=90),
        origin=Origin.HUMAN, authorId=uuid4(), status=ContentStatus.VERIFIED
    )
    p_no_audio.audioRecordings.append(
        AudioRecording(contentId=uuid4(), passageId=p_no_audio.passageId, audioFile="pending.wav",
                       duration=timedelta(seconds=90), authorId=uuid4(), status=ContentStatus.PENDING_REVIEW)
    )
    Passage._registry.append(p_no_audio)

    # 5. VERIFIED passage WITH verified audio (THE ONLY ONE THAT SHOULD APPEAR)
    p_verified = Passage(
        passageId=uuid4(), text="نص معتمد وموثق بتسجيل فصيح",
        level=Level.C1, topic="معتمد تام", duration=timedelta(seconds=100),
        origin=Origin.HUMAN, authorId=uuid4(), status=ContentStatus.VERIFIED
    )
    p_verified.audioRecordings.append(
        AudioRecording(contentId=uuid4(), passageId=p_verified.passageId, audioFile="verified.wav",
                       duration=timedelta(seconds=100), authorId=uuid4(), status=ContentStatus.VERIFIED)
    )
    Passage._registry.append(p_verified)

    # 6. FLAGGED passage (initially verified, then flagged)
    p_flagged = Passage(
        passageId=uuid4(), text="نص مخالف تم حظره",
        level=Level.C2, topic="محظور", duration=timedelta(seconds=110),
        origin=Origin.HUMAN, authorId=uuid4(), status=ContentStatus.FLAGGED
    )
    p_flagged.audioRecordings.append(
        AudioRecording(contentId=uuid4(), passageId=p_flagged.passageId, audioFile="flagged.wav",
                       duration=timedelta(seconds=110), authorId=uuid4(), status=ContentStatus.VERIFIED)
    )
    Passage._registry.append(p_flagged)

    with TestClient(app) as client:
        # Default browse: must return ONLY p_verified
        resp = client.get("/api/passages")
        assert resp.status_code == 200
        passages = resp.json()

        returned_ids = [p["passageId"] for p in passages]
        assert str(p_verified.passageId) in returned_ids, "Verified passage with audio must appear"
        assert str(p_draft.passageId) not in returned_ids, "DRAFT passage must not appear in catalogue"
        assert str(p_claimed.passageId) not in returned_ids, "CLAIMED passage must not appear in catalogue"
        assert str(p_pending.passageId) not in returned_ids, "PENDING_REVIEW passage must not appear in catalogue"
        assert str(p_no_audio.passageId) not in returned_ids, "Passage without verified audio must not appear in catalogue"
        assert str(p_flagged.passageId) not in returned_ids, "FLAGGED passage must not appear in catalogue"
        assert len(passages) == 1, f"Expected exactly 1 verified passage, got: {len(passages)}"

        # include_all=true (for admin): returns all
        resp_all = client.get("/api/passages?include_all=true")
        assert resp_all.status_code == 200
        assert len(resp_all.json()) == 6

def test_flagged_passage_disappears_after_action_taken(tmp_path):
    test_db = str(tmp_path / "test_flag_disappear.db")
    seed_database(test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    with TestClient(app) as client:
        # 1. Login as admin
        admin_login = client.post(
            "/api/auth/login",
            json={"identifier": "admin@asghi.org", "password": "AdminPass123!"}
        )
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["accessToken"]

        # 2. Get verified passages
        resp = client.get("/api/passages")
        assert resp.status_code == 200
        initial_passages = resp.json()
        assert len(initial_passages) >= 1
        target_p = initial_passages[0]
        target_p_id = target_p["passageId"]

        # 3. Learner flags this passage
        learner_login = client.post(
            "/api/auth/login",
            json={"identifier": "learner@asghi.org", "password": "LearnerPass123!"}
        )
        learner_token = learner_login.json()["accessToken"]
        flag_resp = client.post(
            "/api/learner/flag",
            headers={"Authorization": f"Bearer {learner_token}"},
            json={"contentId": target_p_id, "contentType": "PASSAGE", "reason": "Inappropriate content"}
        )
        assert flag_resp.status_code == 200
        flag_id = flag_resp.json()["flagId"]

        # 4. Admin resolves flag with ACTION_TAKEN
        res_resp = client.post(
            f"/api/admin/flags/{flag_id}/resolve",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"newState": "ACTION_TAKEN"}
        )
        assert res_resp.status_code == 200

        # 5. The passage must now disappear from the catalogue
        resp_after = client.get("/api/passages")
        after_ids = [p["passageId"] for p in resp_after.json()]
        assert target_p_id not in after_ids, "Passage must disappear from catalogue after ACTION_TAKEN"

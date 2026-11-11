"""Tests for P1 Item 6 & P3 Item 15:
Verdict atomicity: assignment + feedback + approval count + content status + claim release + reputation in ONE transaction.
Injecting a failure mid-transaction results in zero state mutation and complete rollback.
"""
from datetime import timedelta
import pytest
from asghi.api import get_repository
from asghi.domain.enums import UserRole, Level, ContentStatus, AttributionType
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.domain.reviewer_profile import ReviewerProfile


def test_verdict_atomicity_rollback_on_injected_failure():
    """P3 Item 15: inject a failure mid-transaction -> no assignment, no status change."""
    repo = get_repository()

    # 1. Setup Reviewer
    rev = User(email="rev_atomicity@asghi.org")
    rp: ReviewerProfile = rev.addRole(UserRole.REVIEWER)
    rp.isSpecialist = True
    repo.save_user(rev)

    # 2. Setup Contributor
    con = User(email="con_atomicity@asghi.org")
    con.addRole(UserRole.CONTRIBUTOR)
    repo.save_user(con)

    # 3. Setup Passage with pending recording claimed by contributor
    p = Passage(
        text="نص اختبار ذرية القرار التحكيمي",
        level=Level.B1,
        topic="عام",
        duration=timedelta(seconds=90),
    )
    p.claim(con.userId)
    rec = p.addAudio(
        audioFile="test_atomicity.mp3",
        duration=timedelta(seconds=90),
        attribution=AttributionType.SHOW_NAME,
        authorId=con.userId,
    )
    repo.save_passage(p)

    # Assign review
    assignment = rp.assignReview(rec.contentId)
    repo.save_review_assignment(assignment)

    # Check baseline in DB
    with repo._get_conn() as conn:
        a_row = conn.execute("SELECT is_approved FROM review_assignments WHERE review_id = ?;", (str(assignment.reviewId),)).fetchone()
        assert a_row["is_approved"] is None
        c_row = conn.execute("SELECT status FROM audio_recordings WHERE recording_id = ?;", (str(rec.contentId),)).fetchone()
        assert c_row["status"] == "PENDING_REVIEW"
        p_row = conn.execute("SELECT claimed_by FROM passages WHERE passage_id = ?;", (str(p.passageId),)).fetchone()
        assert p_row["claimed_by"] == str(con.userId)

    # 4. Attempt verdict submission with injected failure
    with pytest.raises(RuntimeError):
        repo.submit_verdict_tx(
            assignment_id=assignment.reviewId,
            reviewer_id=rp.userRoleProfileId,
            is_fusha=True,
            dialect_free=True,
            audio_quality=5,
            is_approved=True,
            reason="ممتاز وفصيح",
            fail_injection=True,
        )

    # 5. Verify complete rollback in SQLite
    with repo._get_conn() as conn:
        # Assignment must remain unapproved
        a_row = conn.execute("SELECT is_approved, is_fusha FROM review_assignments WHERE review_id = ?;", (str(assignment.reviewId),)).fetchone()
        assert a_row["is_approved"] is None, "Assignment should not be approved after rollback"
        assert a_row["is_fusha"] is None or a_row["is_fusha"] == 0

        # Recording must remain PENDING_REVIEW (not VERIFIED)
        c_row = conn.execute("SELECT status FROM audio_recordings WHERE recording_id = ?;", (str(rec.contentId),)).fetchone()
        assert c_row["status"] == "PENDING_REVIEW", "Content status should not change to VERIFIED after rollback"

        # Passage claim must not be released
        p_row = conn.execute("SELECT claimed_by FROM passages WHERE passage_id = ?;", (str(p.passageId),)).fetchone()
        assert p_row["claimed_by"] == str(con.userId), "Claim should not be released after rollback"


def test_verdict_success_commits_all_in_one_transaction():
    """Verify that successful verdict submission updates all tables atomically."""
    repo = get_repository()

    rev = User(email="rev_success@asghi.org")
    rp: ReviewerProfile = rev.addRole(UserRole.REVIEWER)
    rp.isSpecialist = True
    repo.save_user(rev)

    con = User(email="con_success@asghi.org")
    con.addRole(UserRole.CONTRIBUTOR)
    repo.save_user(con)

    p = Passage(text="نص نجاح العملية الذرية", level=Level.B1, topic="عام", duration=timedelta(seconds=90))
    p.claim(con.userId)
    rec = p.addAudio(audioFile="test_success.mp3", duration=timedelta(seconds=90), authorId=con.userId)
    repo.save_passage(p)

    assignment = rp.assignReview(rec.contentId)
    repo.save_review_assignment(assignment)

    success = repo.submit_verdict_tx(
        assignment_id=assignment.reviewId,
        reviewer_id=rp.userRoleProfileId,
        is_fusha=True,
        dialect_free=True,
        audio_quality=5,
        is_approved=True,
        reason="ممتاز وفصيح",
        fail_injection=False,
    )
    assert success is True

    # Verify everything updated atomically in DB
    with repo._get_conn() as conn:
        a_row = conn.execute("SELECT is_approved, is_fusha, audio_quality FROM review_assignments WHERE review_id = ?;", (str(assignment.reviewId),)).fetchone()
        assert a_row["is_approved"] == 1
        assert a_row["is_fusha"] == 1
        assert a_row["audio_quality"] == 5

        c_row = conn.execute("SELECT status FROM audio_recordings WHERE recording_id = ?;", (str(rec.contentId),)).fetchone()
        assert c_row["status"] == "VERIFIED"

        p_row = conn.execute("SELECT claimed_by FROM passages WHERE passage_id = ?;", (str(p.passageId),)).fetchone()
        assert p_row["claimed_by"] is None

        ac_row = conn.execute("SELECT COUNT(*) FROM active_claims WHERE passage_id = ?;", (str(p.passageId),)).fetchone()
        assert ac_row[0] == 0

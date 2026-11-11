"""Tests for P1 Item 5, P3 Item 14 & 18:
- test_claim_race: concurrent claims result in one 200 and one 409
- test_ttl_not_extendable: owner cannot refresh own claim to extend 72h TTL
- test_claim_sweeper: expired claims are released to DRAFT and cleared from active_claims
"""
import concurrent.futures
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from asghi.api import app, get_repository
from asghi.domain.enums import UserRole, Level, ContentStatus
from asghi.domain.user import User
from asghi.domain.passage import Passage
from asghi.security import create_access_token


def test_ttl_not_extendable():
    """Defect 5 / P3 Item 18: claim() must not let holder refresh claimedAt to extend TTL."""
    con_id = uuid4()
    p = Passage(
        text="نص تدريب المهلة الزمنية للحجز",
        level=Level.B1,
        topic="عام",
        duration=timedelta(seconds=90),
    )
    # Initial claim
    assert p.claim(con_id) is True
    initial_time = datetime.now(timezone.utc) - timedelta(hours=20)
    p.claimedAt = initial_time

    # Attempt to re-claim own active claim: must return False and NOT change claimedAt
    reclaim_success = p.claim(con_id)
    assert reclaim_success is False, "Owner must not be allowed to refresh active claim"
    assert p.claimedAt == initial_time, "claimedAt must remain at initial timestamp"


def test_claim_race_concurrent_threads():
    """P1 Item 5 & P3 Item 14: Two concurrent claims -> exactly one 200, one 409."""
    repo = get_repository()
    # Create two contributors
    con1 = User(email="con1_race@asghi.org")
    con1.addRole(UserRole.CONTRIBUTOR)
    repo.save_user(con1)
    tok1 = create_access_token(con1.userId, [UserRole.CONTRIBUTOR])

    con2 = User(email="con2_race@asghi.org")
    con2.addRole(UserRole.CONTRIBUTOR)
    repo.save_user(con2)
    tok2 = create_access_token(con2.userId, [UserRole.CONTRIBUTOR])

    p = Passage(
        text="نص سباق الحجز المتزامن بين متطوعين",
        level=Level.B1,
        topic="عام",
        duration=timedelta(seconds=90),
    )
    repo.save_passage(p)

    client = TestClient(app)

    def do_claim(token):
        return client.post(
            "/api/contributor/claim",
            headers={"Authorization": f"Bearer {token}"},
            json={"passageId": str(p.passageId)}
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(do_claim, tok1)
        f2 = executor.submit(do_claim, tok2)
        res1 = f1.result()
        res2 = f2.result()

    statuses = sorted([res1.status_code, res2.status_code])
    assert statuses == [200, 409], f"Expected exactly [200, 409], got {statuses}"


def test_claim_sweeper_releases_expired_claim():
    """Verify background sweeper releases claims that exceed 72h."""
    repo = get_repository()
    con = User(email="con_sweep@asghi.org")
    con.addRole(UserRole.CONTRIBUTOR)
    repo.save_user(con)

    p = Passage(
        text="نص منتهي الحجز للتنظيف الآلي",
        level=Level.B1,
        topic="عام",
        duration=timedelta(seconds=90),
    )
    p.claim(con.userId)
    # Set claimedAt to 75 hours ago (expired beyond 72h TTL)
    p.claimedAt = datetime.now(timezone.utc) - timedelta(hours=75)
    repo.save_passage(p)

    freed = repo.sweep_expired_claims(ttl_seconds=72 * 3600)
    assert freed >= 1

    # Check passage row in database
    with repo._get_conn() as conn:
        row = conn.execute("SELECT claimed_by, claimed_at, status FROM passages WHERE passage_id = ?;", (str(p.passageId),)).fetchone()
        assert row["claimed_by"] is None
        assert row["status"] == "DRAFT"

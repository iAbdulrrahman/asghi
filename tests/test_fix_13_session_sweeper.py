import os
import sqlite3
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from asghi.repository import get_repository
from asghi.seed import seed_database


def test_abandoned_session_sweeper_marks_stale_sessions_finished(tmp_path):
    test_db = str(tmp_path / "test_sweeper.db")
    seed_database(test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    repo = get_repository()

    # 1. Insert an active session started 25 hours ago with finished_at = NULL
    session_id = str(uuid4())
    learner_id = str(uuid4())

    with sqlite3.connect(test_db) as conn:
        passage_id = conn.execute("SELECT passage_id FROM passages LIMIT 1;").fetchone()[0]
        stale_started_at = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        conn.execute("""
            INSERT INTO test_sessions (session_id, passage_id, learner_id, started_at, finished_at, total_score, current_difficulty)
            VALUES (?, ?, ?, ?, NULL, NULL, 'MEDIUM');
        """, (session_id, passage_id, learner_id, stale_started_at))

    # 2. Run sweeper with 24-hour TTL (86400 seconds)
    closed = repo.sweep_abandoned_sessions(ttl_seconds=86400)
    assert closed >= 1, "Sweeper must close at least 1 abandoned session"

    # 3. Verify in SQLite that finished_at is populated
    with sqlite3.connect(test_db) as conn:
        conn.row_factory = sqlite3.Row
        s_row = conn.execute("SELECT finished_at, total_score FROM test_sessions WHERE session_id = ?", (session_id,)).fetchone()
        assert s_row["finished_at"] is not None, "finished_at must be set after sweeping"
        assert s_row["total_score"] is not None, "total_score must be initialized upon abandonment"

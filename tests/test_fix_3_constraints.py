"""Test DB constraints (P0 Item 3):
- UNIQUE(one active claim per passage)
- UNIQUE(reviewer_id, content_id)
- FK cascade as declared
- CHECK(author_id IS NULL <=> origin='AI')
"""
import sqlite3
import uuid
import pytest
from asghi.repository import Repository


def test_unique_reviewer_content_constraint(tmp_path):
    db_file = str(tmp_path / "test_constraints.db")
    repo = Repository(db_path=db_file)
    content_id = str(uuid.uuid4())
    reviewer_id = str(uuid.uuid4())

    with repo._get_conn() as conn:
        conn.execute("INSERT INTO users (user_id, email) VALUES (?, 'rev@asghi.org');", (reviewer_id,))
        conn.execute("""
            INSERT INTO review_assignments (review_id, content_id, reviewer_id)
            VALUES (?, ?, ?);
        """, (str(uuid.uuid4()), content_id, reviewer_id))

    # Second assignment with same reviewer_id and content_id must fail UNIQUE constraint
    with pytest.raises(sqlite3.IntegrityError):
        with repo._get_conn() as conn:
            conn.execute("""
                INSERT INTO review_assignments (review_id, content_id, reviewer_id)
                VALUES (?, ?, ?);
            """, (str(uuid.uuid4()), content_id, reviewer_id))


def test_check_author_id_origin_equivalence(tmp_path):
    db_file = str(tmp_path / "test_constraints.db")
    repo = Repository(db_path=db_file)
    passage_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    # Valid: AI origin with NULL author_id
    with repo._get_conn() as conn:
        conn.execute("""
            INSERT INTO passages (passage_id, origin, author_id)
            VALUES (?, 'AI', NULL);
        """, (passage_id,))

    # Invalid: AI origin with non-null author_id
    with pytest.raises(sqlite3.IntegrityError):
        with repo._get_conn() as conn:
            conn.execute("""
                INSERT INTO passages (passage_id, origin, author_id)
                VALUES (?, 'AI', ?);
            """, (str(uuid.uuid4()), user_id))

    # Invalid: HUMAN origin with NULL author_id
    with pytest.raises(sqlite3.IntegrityError):
        with repo._get_conn() as conn:
            conn.execute("""
                INSERT INTO passages (passage_id, origin, author_id)
                VALUES (?, 'HUMAN', NULL);
            """, (str(uuid.uuid4()),))


def test_unique_active_claim_per_passage(tmp_path):
    db_file = str(tmp_path / "test_constraints.db")
    repo = Repository(db_path=db_file)
    passage_id = str(uuid.uuid4())
    user_1 = str(uuid.uuid4())
    user_2 = str(uuid.uuid4())

    # Seed passage & users
    with repo._get_conn() as conn:
        conn.execute("INSERT INTO users (user_id, email) VALUES (?, 'u1@asghi.org');", (user_1,))
        conn.execute("INSERT INTO users (user_id, email) VALUES (?, 'u2@asghi.org');", (user_2,))
        conn.execute("INSERT INTO passages (passage_id, origin, author_id) VALUES (?, 'AI', NULL);", (passage_id,))
        conn.execute("INSERT INTO active_claims (passage_id, contributor_id, claimed_at) VALUES (?, ?, CURRENT_TIMESTAMP);", (passage_id, user_1))

    # Second active claim on same passage must fail UNIQUE constraint
    with pytest.raises(sqlite3.IntegrityError):
        with repo._get_conn() as conn:
            conn.execute("INSERT INTO active_claims (passage_id, contributor_id, claimed_at) VALUES (?, ?, CURRENT_TIMESTAMP);", (passage_id, user_2))


def test_foreign_key_cascade(tmp_path):
    db_file = str(tmp_path / "test_constraints.db")
    repo = Repository(db_path=db_file)
    passage_id = str(uuid.uuid4())
    rec_id = str(uuid.uuid4())
    q_id = str(uuid.uuid4())
    sess_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    with repo._get_conn() as conn:
        conn.execute("INSERT INTO users (user_id, email) VALUES (?, 'u@asghi.org');", (user_id,))
        conn.execute("INSERT INTO passages (passage_id, origin, author_id) VALUES (?, 'AI', NULL);", (passage_id,))
        conn.execute("INSERT INTO audio_recordings (recording_id, passage_id, origin, author_id) VALUES (?, ?, 'AI', NULL);", (rec_id, passage_id))
        conn.execute("INSERT INTO questions (question_id, passage_id, origin, author_id) VALUES (?, ?, 'AI', NULL);", (q_id, passage_id))
        conn.execute("INSERT INTO test_sessions (session_id, passage_id, learner_id) VALUES (?, ?, ?);", (sess_id, passage_id, user_id))

    # Now delete passage
    with repo._get_conn() as conn:
        conn.execute("DELETE FROM passages WHERE passage_id = ?;", (passage_id,))

    # Confirm cascade deletion
    with repo._get_conn() as conn:
        assert conn.execute("SELECT COUNT(*) FROM audio_recordings WHERE passage_id = ?;", (passage_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM questions WHERE passage_id = ?;", (passage_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM test_sessions WHERE passage_id = ?;", (passage_id,)).fetchone()[0] == 0

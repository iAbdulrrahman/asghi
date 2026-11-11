import os
import sqlite3
from fastapi.testclient import TestClient

from asghi.api import app
from asghi.domain.enums import ContentStatus, Origin
from asghi.domain.passage import Passage
from asghi.seed import seed_database


def test_ai_generated_content_saved_as_draft(tmp_path):
    test_db = str(tmp_path / "test_ai_draft.db")
    seed_database(test_db)
    os.environ["ASGHI_DB_PATH"] = test_db

    with TestClient(app) as client:
        # Login as Admin
        admin_login = client.post(
            "/api/auth/login",
            json={"identifier": "admin@asghi.org", "password": "AdminPass123!"}
        )
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["accessToken"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Trigger AI Generation
        topic = "الذكاء الاصطناعي وتطبيقاته"
        gen_res = client.post(
            "/api/admin/generate",
            headers=admin_headers,
            json={"topic": topic, "level": "B2"}
        )
        assert gen_res.status_code == 200
        data = gen_res.json()
        passage_id = data["passageId"]

        # Check in DB: passage must have origin = AI and status = DRAFT
        with sqlite3.connect(test_db) as conn:
            conn.row_factory = sqlite3.Row
            p_row = conn.execute("SELECT origin, status FROM passages WHERE passage_id = ?", (passage_id,)).fetchone()
            assert p_row["origin"] == "AI"
            assert p_row["status"] == "DRAFT", f"AI passage must be saved as DRAFT, got {p_row['status']}"

            # Questions must also have status = DRAFT
            q_rows = conn.execute("SELECT origin, status FROM questions WHERE passage_id = ?", (passage_id,)).fetchall()
            assert len(q_rows) > 0
            for q in q_rows:
                assert q["origin"] == "AI"
                assert q["status"] == "DRAFT", f"AI question must be saved as DRAFT, got {q['status']}"

        # Check in memory
        mem_p = next(p for p in Passage._registry if str(p.passageId) == passage_id)
        assert mem_p.origin == Origin.AI
        assert mem_p.status == ContentStatus.DRAFT
        for q in mem_p.questions:
            assert q.origin == Origin.AI
            assert q.status == ContentStatus.DRAFT

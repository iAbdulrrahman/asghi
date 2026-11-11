"""Persistence repository backed by SQLite.
Invention #1: Concrete persistence layer mapping domain entities to SQLite.
"""
from __future__ import annotations
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any
from uuid import UUID

from asghi.domain.enums import (
    UserRole,
    Difficulty,
    Level,
    Origin,
    AttributionType,
    QuestionType,
    ContentStatus,
    FlagStatus,
)
from asghi.domain.user import User
from asghi.domain.user_role_profile import UserRoleProfile
from asghi.domain.learner_profile import LearnerProfile
from asghi.domain.learner_progress import LearnerProgress
from asghi.domain.contributor_profile import ContributorProfile
from asghi.domain.reviewer_profile import ReviewerProfile
from asghi.domain.admin_profile import AdminProfile
from asghi.domain.passage import Passage
from asghi.domain.audio_recording import AudioRecording
from asghi.domain.question import Question
from asghi.domain.review_assignment import ReviewAssignment
from asghi.domain.review_feedback import ReviewFeedback
from asghi.domain.content_flag import ContentFlag
from asghi.domain.test_session import TestSession
from asghi.domain.question_response import QuestionResponse
from asghi.domain.reviewable_content import ReviewableContent

DEFAULT_DB_PATH = "asghi.db"


def get_db_path() -> str:
    return os.environ.get("ASGHI_DB_PATH", DEFAULT_DB_PATH)


def get_repository() -> Repository:
    return Repository(db_path=get_db_path())


class Repository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_db_path()
        self._init_db()

    def clear_all_tables(self) -> None:
        """Clear all tables in database for isolated test fixtures."""
        with self._get_conn() as conn:
            conn.execute("PRAGMA foreign_keys = OFF;")
            conn.execute("DELETE FROM active_claims;")
            conn.execute("DELETE FROM content_flags;")
            conn.execute("DELETE FROM review_assignments;")
            conn.execute("DELETE FROM question_responses;")
            conn.execute("DELETE FROM test_sessions;")
            conn.execute("DELETE FROM questions;")
            conn.execute("DELETE FROM audio_recordings;")
            conn.execute("DELETE FROM passages;")
            conn.execute("DELETE FROM user_profiles;")
            conn.execute("DELETE FROM users;")
            conn.execute("PRAGMA foreign_keys = ON;")




    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys and WAL mode (NFR 14)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT,
                phone_no TEXT,
                display_name TEXT,
                password_hash TEXT,
                arabic_level TEXT,
                status TEXT DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_profiles (
                profile_id TEXT PRIMARY KEY,
                user_id TEXT,
                role TEXT,
                is_specialist INTEGER DEFAULT 0,
                score INTEGER DEFAULT 100,
                approval_rate REAL DEFAULT 1.0,
                total_submissions INTEGER DEFAULT 0,
                learner_total_score INTEGER DEFAULT 0,
                learner_total_time INTEGER DEFAULT 0,
                learner_streak INTEGER DEFAULT 1,
                credits_earned INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS passages (
                passage_id TEXT PRIMARY KEY,
                text TEXT,
                level TEXT,
                topic TEXT,
                duration_seconds REAL,
                claimed_by TEXT,
                claimed_at TEXT,
                author_id TEXT,
                status TEXT,
                origin TEXT,
                rejection_reason TEXT,
                CHECK ((author_id IS NULL AND origin = 'AI') OR (author_id IS NOT NULL AND origin = 'HUMAN'))
            );

            CREATE TABLE IF NOT EXISTS audio_recordings (
                recording_id TEXT PRIMARY KEY,
                passage_id TEXT,
                audio_file TEXT,
                duration_seconds REAL,
                attribution TEXT,
                author_id TEXT,
                status TEXT,
                origin TEXT,
                rejection_reason TEXT,
                FOREIGN KEY (passage_id) REFERENCES passages(passage_id) ON DELETE CASCADE,
                CHECK ((author_id IS NULL AND origin = 'AI') OR (author_id IS NOT NULL AND origin = 'HUMAN'))
            );

            CREATE TABLE IF NOT EXISTS questions (
                question_id TEXT PRIMARY KEY,
                passage_id TEXT,
                prompt_text TEXT,
                answers_json TEXT,
                correct_answer TEXT,
                explanation TEXT,
                passage_reference TEXT,
                difficulty TEXT,
                type TEXT,
                author_id TEXT,
                status TEXT,
                origin TEXT,
                rejection_reason TEXT,
                FOREIGN KEY (passage_id) REFERENCES passages(passage_id) ON DELETE CASCADE,
                CHECK ((author_id IS NULL AND origin = 'AI') OR (author_id IS NOT NULL AND origin = 'HUMAN'))
            );

            CREATE TABLE IF NOT EXISTS active_claims (
                passage_id TEXT PRIMARY KEY,
                contributor_id TEXT NOT NULL,
                claimed_at TIMESTAMP NOT NULL,
                FOREIGN KEY (passage_id) REFERENCES passages(passage_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS review_assignments (
                review_id TEXT PRIMARY KEY,
                content_id TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                created_at TEXT,
                is_specialist INTEGER,
                is_approved INTEGER,
                reason TEXT,
                is_fusha INTEGER,
                dialect_free INTEGER,
                audio_quality INTEGER,
                feedback_text TEXT,
                UNIQUE (reviewer_id, content_id)
            );

            CREATE TABLE IF NOT EXISTS content_flags (
                flag_id TEXT PRIMARY KEY,
                content_id TEXT NOT NULL,
                reporter_id TEXT,
                reason TEXT,
                status TEXT
            );

            CREATE TABLE IF NOT EXISTS test_sessions (
                session_id TEXT PRIMARY KEY,
                passage_id TEXT NOT NULL,
                learner_id TEXT,
                started_at TEXT,
                finished_at TEXT,
                total_score INTEGER,
                current_difficulty TEXT,
                FOREIGN KEY (passage_id) REFERENCES passages(passage_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS question_responses (
                response_id TEXT PRIMARY KEY,
                session_id TEXT,
                question_id TEXT,
                submitted_answer TEXT,
                is_correct INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES test_sessions(session_id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
            );
            """)

    def save_user(self, user: User) -> None:
        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO users (user_id, email, phone_no, display_name, password_hash, arabic_level, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                email=excluded.email,
                phone_no=excluded.phone_no,
                display_name=excluded.display_name,
                password_hash=excluded.password_hash,
                arabic_level=excluded.arabic_level,
                status=excluded.status;
            """, (
                str(user.userId),
                user.email,
                user.phoneNo,
                user.displayName,
                user.passwordHash,
                user.arabicLevel.value if hasattr(user.arabicLevel, 'value') else str(user.arabicLevel),
                user.status,
            ))

            for prof in user.userProfiles:
                is_specialist = 1 if getattr(prof, 'isSpecialist', False) else 0
                rep = getattr(prof, 'reputation', None)
                score = rep.score if rep else 0
                approval_rate = rep.approvalRate if rep else 1.0
                total_subs = rep.totalSubmissions if rep else 0
                credits_earned = getattr(prof, 'creditsEarned', 0)

                prog = getattr(prof, 'progress', None)
                prog_score = prog.totalScore if prog else 0
                prog_time = prog.totalTimeSpent if prog else 0
                prog_streak = prog.currentStreakDays if prog else 1

                conn.execute("""
                INSERT INTO user_profiles (
                    profile_id, user_id, role, is_specialist, score, approval_rate,
                    total_submissions, learner_total_score, learner_total_time,
                    learner_streak, credits_earned
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(profile_id) DO UPDATE SET
                    role=excluded.role,
                    is_specialist=excluded.is_specialist,
                    score=excluded.score,
                    approval_rate=excluded.approval_rate,
                    total_submissions=excluded.total_submissions,
                    learner_total_score=excluded.learner_total_score,
                    learner_total_time=excluded.learner_total_time,
                    learner_streak=excluded.learner_streak,
                    credits_earned=excluded.credits_earned;
                """, (
                    str(prof.userRoleProfileId),
                    str(user.userId),
                    prof.role.value,
                    is_specialist,
                    score,
                    approval_rate,
                    total_subs,
                    prog_score,
                    prog_time,
                    prog_streak,
                    credits_earned,
                ))

    def save_passage(self, passage: Passage) -> None:
        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO passages (
                passage_id, text, level, topic, duration_seconds,
                claimed_by, claimed_at, author_id, status, origin, rejection_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(passage_id) DO UPDATE SET
                text=excluded.text,
                level=excluded.level,
                topic=excluded.topic,
                duration_seconds=excluded.duration_seconds,
                claimed_by=excluded.claimed_by,
                claimed_at=excluded.claimed_at,
                author_id=excluded.author_id,
                status=excluded.status,
                origin=excluded.origin,
                rejection_reason=excluded.rejection_reason;
            """, (
                str(passage.passageId),
                passage.text,
                passage.level.value,
                passage.topic,
                passage.duration.total_seconds(),
                str(passage.claimedBy) if passage.claimedBy else None,
                passage.claimedAt.isoformat() if passage.claimedAt else None,
                str(passage.authorId) if passage.authorId else None,
                passage.status.value,
                passage.origin.value,
                passage.rejectionReason,
            ))
            if passage.claimedBy:
                conn.execute('''
                INSERT INTO active_claims (passage_id, contributor_id, claimed_at)
                VALUES (?, ?, ?)
                ON CONFLICT(passage_id) DO UPDATE SET
                    contributor_id=excluded.contributor_id,
                    claimed_at=excluded.claimed_at;
                ''', (
                    str(passage.passageId),
                    str(passage.claimedBy),
                    passage.claimedAt.isoformat() if passage.claimedAt else datetime.now(timezone.utc).isoformat(),
                ))
            else:
                conn.execute('DELETE FROM active_claims WHERE passage_id = ?;', (str(passage.passageId),))

            for rec in passage.audioRecordings:
                conn.execute("""
                INSERT INTO audio_recordings (
                    recording_id, passage_id, audio_file, duration_seconds,
                    attribution, author_id, status, origin, rejection_reason
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(recording_id) DO UPDATE SET
                    audio_file=excluded.audio_file,
                    duration_seconds=excluded.duration_seconds,
                    attribution=excluded.attribution,
                    author_id=excluded.author_id,
                    status=excluded.status,
                    origin=excluded.origin,
                    rejection_reason=excluded.rejection_reason;
                """, (
                    str(rec.contentId),
                    str(passage.passageId),
                    str(rec.audioFile),
                    rec.duration.total_seconds(),
                    rec.attribution.value,
                    str(rec.authorId) if rec.authorId else None,
                    rec.status.value,
                    rec.origin.value,
                    rec.rejectionReason,
                ))

                for r in rec.reviews:
                    self._save_review_assignment_conn(conn, r)

            for q in passage.questions:
                conn.execute("""
                INSERT INTO questions (
                    question_id, passage_id, prompt_text, answers_json,
                    correct_answer, explanation, passage_reference, difficulty,
                    type, author_id, status, origin, rejection_reason
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(question_id) DO UPDATE SET
                    prompt_text=excluded.prompt_text,
                    answers_json=excluded.answers_json,
                    correct_answer=excluded.correct_answer,
                    explanation=excluded.explanation,
                    passage_reference=excluded.passage_reference,
                    difficulty=excluded.difficulty,
                    type=excluded.type,
                    author_id=excluded.author_id,
                    status=excluded.status,
                    origin=excluded.origin,
                    rejection_reason=excluded.rejection_reason;
                """, (
                    str(q.questionId),
                    str(passage.passageId),
                    q.promptText,
                    json.dumps(q.answers, ensure_ascii=False),
                    q.correctAnswer,
                    q.explanation,
                    q.passageReference,
                    q.difficulty.value,
                    q.type.value,
                    str(q.authorId) if q.authorId else None,
                    q.status.value,
                    q.origin.value,
                    q.rejectionReason,
                ))

                for r in q.reviews:
                    self._save_review_assignment_conn(conn, r)

    def _save_review_assignment_conn(self, conn: sqlite3.Connection, r: ReviewAssignment) -> None:
        fb = r.feedback
        conn.execute("""
        INSERT INTO review_assignments (
            review_id, content_id, reviewer_id, created_at, is_specialist,
            is_approved, reason, is_fusha, dialect_free, audio_quality, feedback_text
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(review_id) DO UPDATE SET
            is_approved=excluded.is_approved,
            reason=excluded.reason,
            is_fusha=excluded.is_fusha,
            dialect_free=excluded.dialect_free,
            audio_quality=excluded.audio_quality,
            feedback_text=excluded.feedback_text;
        """, (
            str(r.reviewId),
            str(r.contentId),
            str(r.reviewerId),
            r.createdAt.isoformat(),
            1 if r.isSpecialistReview else 0,
            1 if r.isApproved is True else (0 if r.isApproved is False else None),
            r.reason,
            1 if (fb and fb.isFusha) else 0,
            1 if (fb and fb.dialectFree) else 0,
            fb.audioQuality if fb else None,
            fb.feedback if fb else None,
        ))

    def save_content_flag(self, flag: ContentFlag) -> None:
        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO content_flags (flag_id, content_id, reporter_id, reason, status)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(flag_id) DO UPDATE SET
                status=excluded.status;
            """, (
                str(flag.flagId),
                str(flag.contentId),
                str(flag.reporterId) if flag.reporterId else None,
                flag.reason,
                flag.status.value,
            ))

    def save_review_assignment(self, r: ReviewAssignment) -> None:
        """Persist review assignment and feedback."""
        with self._get_conn() as conn:
            self._save_review_assignment_conn(conn, r)

    def save_test_session(self, session: TestSession) -> None:
        """Persist learner test session to SQLite."""
        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO test_sessions (
                session_id, passage_id, learner_id, started_at, finished_at, total_score, current_difficulty
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                finished_at=excluded.finished_at,
                total_score=excluded.total_score,
                current_difficulty=excluded.current_difficulty;
            """, (
                str(session.sessionId),
                str(session.passageId),
                str(session.learnerId) if session.learnerId else None,
                session.startedAt.isoformat() if session.startedAt else None,
                session.finishedAt.isoformat() if session.finishedAt else None,
                session.totalScore,
                session.currentDifficulty.value if hasattr(session.currentDifficulty, "value") else str(session.currentDifficulty),
            ))
            for qr in session.questionResponses:
                self._save_question_response_conn(conn, session.sessionId, qr)

    def save_question_response(self, session_id: UUID, qr: QuestionResponse) -> None:
        """Persist individual question response to SQLite."""
        with self._get_conn() as conn:
            self._save_question_response_conn(conn, session_id, qr)

    def _save_question_response_conn(self, conn: sqlite3.Connection, session_id: UUID, qr: QuestionResponse) -> None:
        conn.execute("""
        INSERT INTO question_responses (
            response_id, session_id, question_id, submitted_answer, is_correct
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(response_id) DO UPDATE SET
            submitted_answer=excluded.submitted_answer,
            is_correct=excluded.is_correct;
        """, (
            str(qr.responseId),
            str(session_id),
            str(qr.questionId),
            qr.submittedAnswer,
            1 if qr.isCorrect else 0,
        ))

    def sync_all_to_db(self) -> None:
        """Persist all in-memory domain objects to SQLite."""
        for u in User._registry:
            self.save_user(u)
        for p in Passage._registry:
            self.save_passage(p)
            for f in p.flags:
                self.save_content_flag(f)
            for rec in p.audioRecordings:
                for f in rec.flags:
                    self.save_content_flag(f)
            for q in p.questions:
                for f in q.flags:
                    self.save_content_flag(f)

    def load_all_from_db(self) -> None:
        """Hydrate domain registries from SQLite database."""
        User._registry.clear()
        Passage._registry.clear()
        ReviewableContent._registry.clear()

        with self._get_conn() as conn:
            user_rows = conn.execute("SELECT * FROM users;").fetchall()
            for ur in user_rows:
                u = User(
                    email=ur["email"],
                    phoneNo=ur["phone_no"],
                    displayName=ur["display_name"],
                    passwordHash=ur["password_hash"],
                    arabicLevel=Level(ur["arabic_level"]) if ur["arabic_level"] else Level.A1,
                    userId=UUID(ur["user_id"]),
                )
                u.status = ur["status"] or "ACTIVE"

                prof_rows = conn.execute(
                    "SELECT * FROM user_profiles WHERE user_id = ?;", (ur["user_id"],)
                ).fetchall()
                for pr in prof_rows:
                    role = UserRole(pr["role"])
                    prof = u.addRole(role)
                    prof.userRoleProfileId = UUID(pr["profile_id"])
                    if hasattr(prof, "isSpecialist"):
                        prof.isSpecialist = bool(pr["is_specialist"])
                    if hasattr(prof, "creditsEarned"):
                        prof.creditsEarned = pr["credits_earned"]
                    if hasattr(prof, "reputation") and prof.reputation:
                        prof.reputation.score = pr["score"]
                        prof.reputation.approvalRate = pr["approval_rate"]
                        prof.reputation.totalSubmissions = pr["total_submissions"]
                    if hasattr(prof, "progress") and prof.progress:
                        prof.progress.totalScore = pr["learner_total_score"]
                        prof.progress.totalTimeSpent = pr["learner_total_time"]
                        prof.progress.currentStreakDays = pr["learner_streak"]

            passage_rows = conn.execute("SELECT * FROM passages;").fetchall()
            for pr in passage_rows:
                p = Passage(
                    text=pr["text"],
                    level=Level(pr["level"]),
                    topic=pr["topic"],
                    duration=timedelta(seconds=pr["duration_seconds"] or 90),
                    passageId=UUID(pr["passage_id"]),
                    claimedBy=UUID(pr["claimed_by"]) if pr["claimed_by"] else None,
                    claimedAt=datetime.fromisoformat(pr["claimed_at"]) if pr["claimed_at"] else None,
                    authorId=UUID(pr["author_id"]) if pr["author_id"] else None,
                    status=ContentStatus(pr["status"]),
                    origin=Origin(pr["origin"]),
                )
                p.rejectionReason = pr["rejection_reason"]

                # Load recordings
                rec_rows = conn.execute(
                    "SELECT * FROM audio_recordings WHERE passage_id = ?;", (pr["passage_id"],)
                ).fetchall()
                for rr in rec_rows:
                    rec = AudioRecording(
                        audioFile=rr["audio_file"],
                        duration=timedelta(seconds=rr["duration_seconds"] or 90),
                        attribution=AttributionType(rr["attribution"]),
                        passageId=p.passageId,
                        authorId=UUID(rr["author_id"]) if rr["author_id"] else None,
                        contentId=UUID(rr["recording_id"]),
                        status=ContentStatus(rr["status"]),
                        origin=Origin(rr["origin"]),
                    )
                    rec.rejectionReason = rr["rejection_reason"]
                    p.audioRecordings.append(rec)

                # Load questions
                q_rows = conn.execute(
                    "SELECT * FROM questions WHERE passage_id = ?;", (pr["passage_id"],)
                ).fetchall()
                for qr in q_rows:
                    answers = json.loads(qr["answers_json"]) if qr["answers_json"] else []
                    q = Question(
                        promptText=qr["prompt_text"],
                        answers=answers,
                        correctAnswer=qr["correct_answer"],
                        explanation=qr["explanation"],
                        passageReference=qr["passage_reference"] or "",
                        difficulty=Difficulty(qr["difficulty"]),
                        type=QuestionType(qr["type"]),
                        passageId=p.passageId,
                        authorId=UUID(qr["author_id"]) if qr["author_id"] else None,
                        contentId=UUID(qr["question_id"]),
                        status=ContentStatus(qr["status"]),
                        origin=Origin(qr["origin"]),
                    )
                    q.rejectionReason = qr["rejection_reason"]
                    p.questions.append(q)

                # Load flags
                flag_rows = conn.execute(
                    "SELECT * FROM content_flags WHERE content_id = ?;", (pr["passage_id"],)
                ).fetchall()
                for fr in flag_rows:
                    flag = ContentFlag(
                        contentId=p.passageId,
                        reason=fr["reason"],
                        reporterId=UUID(fr["reporter_id"]) if fr["reporter_id"] else None,
                        flagId=UUID(fr["flag_id"]),
                        status=FlagStatus(fr["status"]),
                    )
                    p.flags.append(flag)

            # Hydrate review assignments onto content
            rev_rows = conn.execute("SELECT * FROM review_assignments;").fetchall()
            for r_row in rev_rows:
                c_id = UUID(r_row["content_id"])
                target_c = None
                for p in Passage._registry:
                    if p.contentId == c_id:
                        target_c = p
                        break
                    for rec in p.audioRecordings:
                        if rec.contentId == c_id:
                            target_c = rec
                            break
                    for q in p.questions:
                        if q.contentId == c_id:
                            target_c = q
                            break
                if not target_c:
                    for item in ReviewableContent._registry:
                        if item.contentId == c_id:
                            target_c = item
                            break

                assignment = ReviewAssignment(
                    reviewerId=UUID(r_row["reviewer_id"]),
                    contentId=c_id,
                    isSpecialistReview=bool(r_row["is_specialist"]),
                    reviewId=UUID(r_row["review_id"]),
                    createdAt=datetime.fromisoformat(r_row["created_at"]) if r_row["created_at"] else None,
                )
                assignment.isApproved = True if r_row["is_approved"] == 1 else (False if r_row["is_approved"] == 0 else None)
                assignment.reason = r_row["reason"]
                assignment.feedback = ReviewFeedback(
                    isFusha=bool(r_row["is_fusha"]),
                    dialectFree=bool(r_row["dialect_free"]),
                    audioQuality=r_row["audio_quality"],
                    feedback=r_row["feedback_text"] or "",
                )
                if target_c and not any(ra.reviewId == assignment.reviewId for ra in target_c.reviews):
                    target_c.reviews.append(assignment)


    def _hydrate_user(self, conn: sqlite3.Connection, ur: sqlite3.Row) -> User:
        for u in User._registry:
            if str(u.userId) == ur["user_id"]:
                return u
        u = User(
            email=ur["email"],
            phoneNo=ur["phone_no"],
            displayName=ur["display_name"],
            passwordHash=ur["password_hash"],
            arabicLevel=Level(ur["arabic_level"]) if ur["arabic_level"] else Level.A1,
            userId=UUID(ur["user_id"]),
        )
        u.status = ur["status"] or "ACTIVE"
        prof_rows = conn.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?;", (ur["user_id"],)
        ).fetchall()
        for pr in prof_rows:
            role = UserRole(pr["role"])
            prof = u.addRole(role)
            prof.userRoleProfileId = UUID(pr["profile_id"])
            if hasattr(prof, "isSpecialist"):
                prof.isSpecialist = bool(pr["is_specialist"])
            if hasattr(prof, "creditsEarned"):
                prof.creditsEarned = pr["credits_earned"]
            if hasattr(prof, "reputation") and prof.reputation:
                prof.reputation.score = pr["score"]
                prof.reputation.approvalRate = pr["approval_rate"]
                prof.reputation.totalSubmissions = pr["total_submissions"]
            if hasattr(prof, "progress") and prof.progress:
                prof.progress.totalScore = pr["learner_total_score"]
                prof.progress.totalTimeSpent = pr["learner_total_time"]
                prof.progress.currentStreakDays = pr["learner_streak"]
        return u

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        for u in User._registry:
            if u.userId == user_id:
                self.save_user(u)
                return u
        with self._get_conn() as conn:
            ur = conn.execute("SELECT * FROM users WHERE user_id = ?;", (str(user_id),)).fetchone()
            if not ur:
                return None
            return self._hydrate_user(conn, ur)

    def get_user_by_identifier(self, identifier: str) -> Optional[User]:
        ident = identifier.strip()
        for u in User._registry:
            if (u.email and u.email.lower() == ident.lower()) or (u.phoneNo and u.phoneNo == ident):
                return u
        with self._get_conn() as conn:
            ur = conn.execute(
                "SELECT * FROM users WHERE LOWER(email) = LOWER(?) OR phone_no = ?;",
                (ident, ident),
            ).fetchone()
            if not ur:
                return None
            return self._hydrate_user(conn, ur)

    def get_passage_by_id(self, passage_id: UUID) -> Optional[Passage]:
        for p in Passage._registry:
            if p.passageId == passage_id:
                self.save_passage(p)
                return p
        self.load_all_from_db()
        for p in Passage._registry:
            if p.passageId == passage_id:
                return p
        return None


-- Asghi (اصغِ) — SQLite schema
-- Generated from asghi/repository.py; every statement is idempotent.

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

-- Lookup and uniqueness indexes (ISO/IEC 25010 time behaviour)
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone_no);
CREATE INDEX IF NOT EXISTS idx_passages_status ON passages(status);
CREATE INDEX IF NOT EXISTS idx_passages_level ON passages(level);
CREATE INDEX IF NOT EXISTS idx_recordings_passage ON audio_recordings(passage_id);
CREATE INDEX IF NOT EXISTS idx_questions_passage ON questions(passage_id);
CREATE INDEX IF NOT EXISTS idx_sessions_learner ON test_sessions(learner_id);
CREATE INDEX IF NOT EXISTS idx_responses_session ON question_responses(session_id);
CREATE INDEX IF NOT EXISTS idx_reviews_content ON review_assignments(content_id);
CREATE INDEX IF NOT EXISTS idx_flags_status ON content_flags(status);

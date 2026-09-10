"""
SQLite database connection and schema initialisation.

Replaces the previous MongoDB/PyMongo layer.
No database server is required — SQLite is bundled with Python.
"""
import sqlite3
import logging
import os
from config import Config

logger = logging.getLogger(__name__)


def get_db_connection() -> sqlite3.Connection:
    """Return an open SQLite connection with Row factory and FK enforcement."""
    conn = sqlite3.connect(Config.db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # better concurrent access
    return conn


def init_db():
    """Create all tables and indexes if they do not already exist."""
    db_path = Config.db_path()
    logger.info(f"Initialising SQLite database at: {db_path}")
    parent = os.path.dirname(os.path.abspath(db_path))
    if parent:
        os.makedirs(parent, exist_ok=True)

    ddl = """
    -- ── users ──────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT    NOT NULL,
        email         TEXT    UNIQUE NOT NULL,
        password_hash TEXT    NOT NULL,
        exam_dates    TEXT    DEFAULT '{}',
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

    -- ── subjects ────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS subjects (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL,
        name        TEXT    NOT NULL,
        description TEXT    DEFAULT '',
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_subjects_user ON subjects(user_id);

    -- ── documents ───────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS documents (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL,
        subject_id   INTEGER NOT NULL DEFAULT 0,
        filename     TEXT    NOT NULL,
        file_path    TEXT    NOT NULL,
        status       TEXT    DEFAULT 'uploaded',
        page_count   INTEGER DEFAULT 0,
        chunk_count  INTEGER DEFAULT 0,
        uploaded_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_docs_user    ON documents(user_id);
    CREATE INDEX IF NOT EXISTS idx_docs_subject ON documents(subject_id);

    -- ── quizzes ─────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS quizzes (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL,
        subject_id INTEGER NOT NULL DEFAULT 0,
        topic      TEXT    DEFAULT '',
        questions  TEXT    NOT NULL,   -- JSON array
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_quizzes_user    ON quizzes(user_id);
    CREATE INDEX IF NOT EXISTS idx_quizzes_subject ON quizzes(subject_id);

    -- ── quiz_attempts ────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id        INTEGER NOT NULL,
        quiz_id        INTEGER NOT NULL,
        score          INTEGER DEFAULT 0,
        total_questions INTEGER DEFAULT 0,
        percentage     REAL    DEFAULT 0,
        answers        TEXT    DEFAULT '[]',  -- JSON
        weak_topics    TEXT    DEFAULT '[]',  -- JSON
        attempted_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_attempts_user ON quiz_attempts(user_id);

    -- ── progress ────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS progress (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id       INTEGER NOT NULL,
        subject_id    INTEGER NOT NULL DEFAULT 0,
        topic         TEXT    NOT NULL,
        quiz_score    REAL    DEFAULT 0,
        attempt_count INTEGER DEFAULT 0,
        strength      TEXT    DEFAULT 'unknown',
        last_updated  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id, subject_id, topic),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_progress_user ON progress(user_id);

    -- ── study_plans ──────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS study_plans (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL,
        subject_id   INTEGER NOT NULL DEFAULT 0,
        tasks        TEXT    NOT NULL,  -- JSON array
        duration_days INTEGER DEFAULT 7,
        exam_date    TEXT    DEFAULT '',
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_plans_user ON study_plans(user_id);

    -- ── flashcards ───────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS flashcards (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL,
        subject_id INTEGER NOT NULL DEFAULT 0,
        topic      TEXT    DEFAULT '',
        question   TEXT    NOT NULL,
        answer     TEXT    NOT NULL,
        difficulty TEXT    DEFAULT 'medium',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_flashcards_user    ON flashcards(user_id);
    CREATE INDEX IF NOT EXISTS idx_flashcards_subject ON flashcards(subject_id);

    -- ── chat_history ─────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS chat_history (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL,
        subject_id INTEGER NOT NULL DEFAULT 0,
        question   TEXT    NOT NULL,
        intent     TEXT    DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_history(user_id);
    """

    try:
        conn = get_db_connection()
        # Execute each statement separately (sqlite3 executescript doesn't use the
        # PRAGMA foreign_keys from the connection — but DDL doesn't need it)
        for stmt in [s.strip() for s in ddl.split(";") if s.strip()]:
            conn.execute(stmt)
        conn.commit()
        conn.close()
        logger.info("SQLite schema ready.")
    except Exception as exc:
        logger.error(f"Database initialisation failed: {exc}")
        raise

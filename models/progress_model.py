"""
Progress model — SQLite CRUD helpers for the progress table.
"""
import logging
from models.db import get_db_connection

logger = logging.getLogger(__name__)


def upsert_topic_progress(user_id, subject_id, topic: str,
                          quiz_score: float, strength: str):
    conn = get_db_connection()
    try:
        # UPSERT: update if row exists (unique on user_id+subject_id+topic)
        conn.execute(
            """INSERT INTO progress (user_id, subject_id, topic, quiz_score, strength, attempt_count, last_updated)
               VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
               ON CONFLICT(user_id, subject_id, topic)
               DO UPDATE SET
                   quiz_score    = excluded.quiz_score,
                   strength      = excluded.strength,
                   attempt_count = attempt_count + 1,
                   last_updated  = CURRENT_TIMESTAMP""",
            (int(user_id), int(subject_id) if subject_id else 0,
             topic, quiz_score, strength),
        )
        conn.commit()
    finally:
        conn.close()


def get_progress_for_user(user_id, subject_id=None) -> list:
    conn = get_db_connection()
    try:
        if subject_id:
            rows = conn.execute(
                "SELECT * FROM progress WHERE user_id = ? AND subject_id = ? ORDER BY last_updated DESC",
                (int(user_id), int(subject_id)),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM progress WHERE user_id = ? ORDER BY last_updated DESC",
                (int(user_id),),
            ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def get_weak_topics(user_id, subject_id=None, threshold: float = 50.0) -> list:
    progress = get_progress_for_user(user_id, subject_id)
    return [p["topic"] for p in progress if p.get("quiz_score", 100) < threshold]


def get_strong_topics(user_id, subject_id=None, threshold: float = 70.0) -> list:
    progress = get_progress_for_user(user_id, subject_id)
    return [p["topic"] for p in progress if p.get("quiz_score", 0) >= threshold]


def serialize_progress(p: dict) -> dict:
    return {
        "id": str(p["id"]),
        "topic": p.get("topic", ""),
        "subject_id": str(p.get("subject_id", "")),
        "quiz_score": p.get("quiz_score", 0),
        "strength": p.get("strength", "unknown"),
        "attempt_count": p.get("attempt_count", 0),
        "last_updated": p.get("last_updated", ""),
    }

"""
Quiz model — SQLite CRUD helpers for quizzes and quiz_attempts tables.
"""
import json
import logging
from models.db import get_db_connection

logger = logging.getLogger(__name__)


def create_quiz(user_id, subject_id, topic: str, questions: list) -> dict:
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "INSERT INTO quizzes (user_id, subject_id, topic, questions) VALUES (?, ?, ?, ?)",
            (int(user_id), int(subject_id) if subject_id else 0,
             topic, json.dumps(questions)),
        )
        conn.commit()
        quiz_id = cur.lastrowid
    finally:
        conn.close()
    return get_quiz(quiz_id, user_id)


def get_quizzes_for_user(user_id, subject_id=None) -> list:
    conn = get_db_connection()
    try:
        if subject_id:
            rows = conn.execute(
                "SELECT * FROM quizzes WHERE user_id = ? AND subject_id = ? ORDER BY created_at DESC",
                (int(user_id), int(subject_id)),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM quizzes WHERE user_id = ? ORDER BY created_at DESC",
                (int(user_id),),
            ).fetchall()
    finally:
        conn.close()
    return [_parse_quiz(dict(r)) for r in rows]


def get_quiz(quiz_id, user_id) -> dict | None:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM quizzes WHERE id = ? AND user_id = ?",
            (int(quiz_id), int(user_id)),
        ).fetchone()
    finally:
        conn.close()
    return _parse_quiz(dict(row)) if row else None


def _parse_quiz(q: dict) -> dict:
    """Deserialise the JSON questions field."""
    if isinstance(q.get("questions"), str):
        try:
            q["questions"] = json.loads(q["questions"])
        except (json.JSONDecodeError, TypeError):
            q["questions"] = []
    return q


def save_quiz_attempt(user_id, quiz_id, score: int, total: int,
                      answers: list, weak_topics: list) -> dict:
    percentage = round(score / total * 100, 1) if total else 0
    conn = get_db_connection()
    try:
        cur = conn.execute(
            """INSERT INTO quiz_attempts
               (user_id, quiz_id, score, total_questions, percentage, answers, weak_topics)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (int(user_id), int(quiz_id), score, total, percentage,
             json.dumps(answers), json.dumps(weak_topics)),
        )
        conn.commit()
        attempt_id = cur.lastrowid
    finally:
        conn.close()
    return get_attempt(attempt_id)


def get_attempt(attempt_id) -> dict:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM quiz_attempts WHERE id = ?", (int(attempt_id),)
        ).fetchone()
    finally:
        conn.close()
    return _parse_attempt(dict(row)) if row else {}


def get_attempts_for_user(user_id, quiz_id=None) -> list:
    conn = get_db_connection()
    try:
        if quiz_id:
            rows = conn.execute(
                "SELECT * FROM quiz_attempts WHERE user_id = ? AND quiz_id = ? ORDER BY attempted_at DESC",
                (int(user_id), int(quiz_id)),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM quiz_attempts WHERE user_id = ? ORDER BY attempted_at DESC",
                (int(user_id),),
            ).fetchall()
    finally:
        conn.close()
    return [_parse_attempt(dict(r)) for r in rows]


def _parse_attempt(a: dict) -> dict:
    for field in ("answers", "weak_topics"):
        if isinstance(a.get(field), str):
            try:
                a[field] = json.loads(a[field])
            except (json.JSONDecodeError, TypeError):
                a[field] = []
    return a


def serialize_quiz(q: dict, include_answers: bool = False) -> dict:
    questions = []
    for qu in q.get("questions", []):
        qd = {
            "question": qu.get("question", ""),
            "options": qu.get("options", []),
            "topic": qu.get("topic", ""),
            "difficulty": qu.get("difficulty", ""),
            "explanation": qu.get("explanation", ""),
        }
        if include_answers:
            qd["correct_answer"] = qu.get("correct_answer", "")
        questions.append(qd)
    return {
        "id": str(q["id"]),
        "user_id": str(q.get("user_id", "")),
        "subject_id": str(q.get("subject_id", "")),
        "topic": q.get("topic", ""),
        "questions": questions,
        "created_at": q.get("created_at", ""),
    }

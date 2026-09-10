"""
User model — SQLite CRUD helpers for the users table.
"""
import json
import logging
from datetime import datetime
import bcrypt
from models.db import get_db_connection

logger = logging.getLogger(__name__)


def create_user(name: str, email: str, password: str) -> dict:
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email.lower().strip(), password_hash),
        )
        conn.commit()
        user_id = cur.lastrowid
    finally:
        conn.close()
    return find_user_by_id(user_id)


def find_user_by_email(email: str) -> dict | None:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def find_user_by_id(user_id) -> dict | None:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (int(user_id),)
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def update_exam_date(user_id, subject_name: str, exam_date: str):
    user = find_user_by_id(user_id)
    if not user:
        return
    try:
        dates = json.loads(user.get("exam_dates") or "{}")
    except (json.JSONDecodeError, TypeError):
        dates = {}
    dates[subject_name] = exam_date
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE users SET exam_dates = ? WHERE id = ?",
            (json.dumps(dates), int(user_id)),
        )
        conn.commit()
    finally:
        conn.close()


def serialize_user(user: dict) -> dict:
    try:
        exam_dates = json.loads(user.get("exam_dates") or "{}")
    except (json.JSONDecodeError, TypeError):
        exam_dates = {}
    return {
        "id": str(user["id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "created_at": user.get("created_at", ""),
        "exam_dates": exam_dates,
    }

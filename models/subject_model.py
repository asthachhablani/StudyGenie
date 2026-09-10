"""
Subject model — SQLite CRUD helpers for the subjects table.
"""
import logging
from models.db import get_db_connection

logger = logging.getLogger(__name__)


def create_subject(user_id, name: str, description: str = "") -> dict:
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "INSERT INTO subjects (user_id, name, description) VALUES (?, ?, ?)",
            (int(user_id), name.strip(), description.strip()),
        )
        conn.commit()
        subject_id = cur.lastrowid
    finally:
        conn.close()
    return get_subject(subject_id, user_id)


def get_subjects_for_user(user_id) -> list:
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM subjects WHERE user_id = ? ORDER BY created_at DESC",
            (int(user_id),),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def get_subject(subject_id, user_id) -> dict | None:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM subjects WHERE id = ? AND user_id = ?",
            (int(subject_id), int(user_id)),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def update_subject(subject_id, user_id, name: str, description: str) -> bool:
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "UPDATE subjects SET name = ?, description = ? WHERE id = ? AND user_id = ?",
            (name.strip(), description.strip(), int(subject_id), int(user_id)),
        )
        conn.commit()
    finally:
        conn.close()
    return cur.rowcount > 0


def delete_subject(subject_id, user_id) -> bool:
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "DELETE FROM subjects WHERE id = ? AND user_id = ?",
            (int(subject_id), int(user_id)),
        )
        conn.commit()
    finally:
        conn.close()
    return cur.rowcount > 0


def serialize_subject(s: dict) -> dict:
    return {
        "id": str(s["id"]),
        "user_id": str(s.get("user_id", "")),
        "name": s.get("name", ""),
        "description": s.get("description", ""),
        "created_at": s.get("created_at", ""),
    }

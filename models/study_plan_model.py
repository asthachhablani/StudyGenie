"""
Study Plan model — SQLite CRUD helpers for the study_plans table.
"""
import json
import logging
from models.db import get_db_connection

logger = logging.getLogger(__name__)


def create_study_plan(user_id, subject_id, tasks: list,
                      duration_days: int, exam_date: str = None) -> dict:
    conn = get_db_connection()
    try:
        cur = conn.execute(
            """INSERT INTO study_plans (user_id, subject_id, tasks, duration_days, exam_date)
               VALUES (?, ?, ?, ?, ?)""",
            (int(user_id), int(subject_id) if subject_id else 0,
             json.dumps(tasks), duration_days, exam_date or ""),
        )
        conn.commit()
        plan_id = cur.lastrowid
    finally:
        conn.close()
    return get_plan(plan_id)


def get_plan(plan_id) -> dict | None:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM study_plans WHERE id = ?", (int(plan_id),)
        ).fetchone()
    finally:
        conn.close()
    return _parse_plan(dict(row)) if row else None


def get_latest_plan(user_id, subject_id=None) -> dict | None:
    conn = get_db_connection()
    try:
        if subject_id:
            row = conn.execute(
                "SELECT * FROM study_plans WHERE user_id = ? AND subject_id = ? ORDER BY created_at DESC LIMIT 1",
                (int(user_id), int(subject_id)),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM study_plans WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (int(user_id),),
            ).fetchone()
    finally:
        conn.close()
    return _parse_plan(dict(row)) if row else None


def get_plans_for_user(user_id) -> list:
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM study_plans WHERE user_id = ? ORDER BY created_at DESC",
            (int(user_id),),
        ).fetchall()
    finally:
        conn.close()
    return [_parse_plan(dict(r)) for r in rows]


def mark_task_complete(plan_id, user_id, task_index: int):
    plan = get_plan(plan_id)
    if not plan or str(plan.get("user_id")) != str(user_id):
        return
    tasks = plan.get("tasks", [])
    # tasks is a list of day-objects; task_index is a task within the first day
    if tasks and isinstance(tasks[0], dict):
        day_tasks = tasks[0].get("tasks", [])
        if task_index < len(day_tasks):
            day_tasks[task_index]["completed"] = True
            tasks[0]["tasks"] = day_tasks
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE study_plans SET tasks = ? WHERE id = ? AND user_id = ?",
            (json.dumps(tasks), int(plan_id), int(user_id)),
        )
        conn.commit()
    finally:
        conn.close()


def _parse_plan(p: dict) -> dict:
    if isinstance(p.get("tasks"), str):
        try:
            p["tasks"] = json.loads(p["tasks"])
        except (json.JSONDecodeError, TypeError):
            p["tasks"] = []
    return p


def serialize_plan(p: dict) -> dict:
    return {
        "id": str(p["id"]),
        "user_id": str(p.get("user_id", "")),
        "subject_id": str(p.get("subject_id", "")),
        "tasks": p.get("tasks", []),
        "duration_days": p.get("duration_days", 0),
        "exam_date": p.get("exam_date", ""),
        "created_at": p.get("created_at", ""),
    }

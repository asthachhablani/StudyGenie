"""
Dashboard routes — aggregate stats for the authenticated student.
"""
import logging
from flask import Blueprint, request, jsonify
from models.auth import login_required, get_current_user_id
from models.subject_model import get_subjects_for_user
from models.document_model import get_documents_for_user
from models.quiz_model import get_quizzes_for_user, get_attempts_for_user
from models.progress_model import get_weak_topics, get_strong_topics, get_progress_for_user
from models.study_plan_model import get_latest_plan, serialize_plan

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("", methods=["GET"])
@login_required
def dashboard():
    user_id = get_current_user_id()

    subjects = get_subjects_for_user(user_id)
    documents = get_documents_for_user(user_id)
    quizzes = get_quizzes_for_user(user_id)
    attempts = get_attempts_for_user(user_id)
    progress = get_progress_for_user(user_id)
    weak = get_weak_topics(user_id)
    strong = get_strong_topics(user_id)
    latest_plan = get_latest_plan(user_id)

    # Average quiz score
    avg_score = 0.0
    if attempts:
        avg_score = round(sum(a.get("percentage", 0) for a in attempts) / len(attempts), 1)

    # Topics completed (strength = strong)
    topics_completed = len([p for p in progress if p.get("strength") == "strong"])

    # Today's tasks from latest plan
    today_tasks = []
    if latest_plan:
        tasks_data = latest_plan.get("tasks", [])
        if tasks_data and isinstance(tasks_data, list):
            for day in tasks_data[:1]:  # First incomplete day
                if isinstance(day, dict):
                    today_tasks = day.get("tasks", [])
                    break

    # Recent quiz results
    recent_results = []
    for a in attempts[:5]:
        recent_results.append({
            "score": a.get("score", 0),
            "total": a.get("total_questions", 0),
            "percentage": a.get("percentage", 0),
            "attempted_at": a.get("attempted_at", ""),
            "weak_topics": a.get("weak_topics", []),
        })

    # Performance trend
    trend = "improving" if (len(attempts) >= 2 and
                            attempts[0].get("percentage", 0) > attempts[-1].get("percentage", 0)) \
        else "stable"

    from models.user_model import find_user_by_id
    user = find_user_by_id(user_id)
    exam_dates = user.get("exam_dates", {}) if user else {}

    return jsonify({
        "stats": {
            "total_subjects": len(subjects),
            "total_documents": len(documents),
            "total_quizzes": len(quizzes),
            "total_attempts": len(attempts),
            "avg_score": avg_score,
            "topics_completed": topics_completed,
        },
        "weak_topics": weak[:5],
        "strong_topics": strong[:5],
        "today_tasks": today_tasks[:5],
        "recent_results": recent_results,
        "latest_plan": serialize_plan(latest_plan) if latest_plan else None,
        "performance_trend": trend,
        "exam_dates": exam_dates,
        "subjects": [{"id": str(s["id"]), "name": s["name"]} for s in subjects],
    }), 200


@dashboard_bp.route("/progress", methods=["GET"])
@login_required
def progress_overview():
    user_id = get_current_user_id()
    subject_id = request.args.get("subject_id")
    progress = get_progress_for_user(user_id, subject_id)
    from models.progress_model import serialize_progress
    return jsonify({"progress": [serialize_progress(p) for p in progress]}), 200


@dashboard_bp.route("/exam-date", methods=["POST"])
@login_required
def set_exam_date():
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}
    subject_name = (data.get("subject_name") or "").strip()
    exam_date = (data.get("exam_date") or "").strip()
    if not subject_name or not exam_date:
        return jsonify({"error": "subject_name and exam_date required"}), 400
    from models.user_model import update_exam_date
    update_exam_date(user_id, subject_name, exam_date)
    return jsonify({"message": "Exam date saved"}), 200

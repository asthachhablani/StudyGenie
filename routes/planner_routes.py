"""
Planner routes — generate and manage study plans.
"""
import logging
from flask import Blueprint, request, jsonify
from models.auth import login_required, get_current_user_id
from models.study_plan_model import (get_plans_for_user, get_latest_plan,
                                      mark_task_complete, serialize_plan)
from agents.study_planner_agent import StudyPlannerAgent

logger = logging.getLogger(__name__)
planner_bp = Blueprint("planner", __name__)


@planner_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}
    subject_id = (data.get("subject_id") or "").strip()
    hours_per_day = float(data.get("hours_per_day", 2))
    duration_days = min(int(data.get("duration_days", 7)), 30)
    exam_date = data.get("exam_date")

    agent = StudyPlannerAgent()
    result = agent.create_plan(user_id, subject_id, hours_per_day, duration_days, exam_date)

    if result.get("error"):
        return jsonify(result), 503
    return jsonify(result), 201


@planner_bp.route("", methods=["GET"])
@login_required
def list_plans():
    user_id = get_current_user_id()
    plans = get_plans_for_user(user_id)
    return jsonify({"plans": [serialize_plan(p) for p in plans]}), 200


@planner_bp.route("/latest", methods=["GET"])
@login_required
def latest():
    user_id = get_current_user_id()
    subject_id = request.args.get("subject_id")
    plan = get_latest_plan(user_id, subject_id)
    if not plan:
        return jsonify({"plan": None}), 200
    return jsonify({"plan": serialize_plan(plan)}), 200


@planner_bp.route("/<plan_id>/task/<int:task_index>/complete", methods=["POST"])
@login_required
def complete_task(plan_id, task_index):
    user_id = get_current_user_id()
    mark_task_complete(plan_id, user_id, task_index)
    return jsonify({"message": "Task marked as complete"}), 200

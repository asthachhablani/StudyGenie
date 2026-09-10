"""
Quiz routes — generate, retrieve, submit quizzes.
"""
import logging
from flask import Blueprint, request, jsonify
from models.auth import login_required, get_current_user_id
from models.quiz_model import get_quizzes_for_user, get_quiz, get_attempts_for_user, serialize_quiz
from agents.quiz_agent import QuizAgent
from agents.weak_area_agent import WeakAreaAgent

logger = logging.getLogger(__name__)
quiz_bp = Blueprint("quizzes", __name__)


@quiz_bp.route("", methods=["GET"])
@login_required
def list_quizzes():
    user_id = get_current_user_id()
    subject_id = request.args.get("subject_id")
    quizzes = get_quizzes_for_user(user_id, subject_id)
    return jsonify({"quizzes": [serialize_quiz(q) for q in quizzes]}), 200


@quiz_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}
    subject_id = (data.get("subject_id") or "").strip()
    topic = (data.get("topic") or "").strip()
    count = min(int(data.get("count", 10)), 20)
    difficulty = data.get("difficulty", "medium")

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    agent = QuizAgent()
    result = agent.generate(user_id, subject_id, topic, count=count, difficulty=difficulty)

    if result.get("error"):
        return jsonify(result), 503
    return jsonify(result), 201


@quiz_bp.route("/<quiz_id>", methods=["GET"])
@login_required
def get_one(quiz_id):
    user_id = get_current_user_id()
    quiz = get_quiz(quiz_id, user_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404
    return jsonify({"quiz": serialize_quiz(quiz)}), 200


@quiz_bp.route("/<quiz_id>/submit", methods=["POST"])
@login_required
def submit(quiz_id):
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}
    answers = data.get("answers", [])

    if not answers:
        return jsonify({"error": "No answers submitted"}), 400

    agent = QuizAgent()
    result = agent.score(user_id, quiz_id, answers)

    if result.get("error"):
        return jsonify(result), 404
    return jsonify(result), 200


@quiz_bp.route("/attempts", methods=["GET"])
@login_required
def attempts():
    user_id = get_current_user_id()
    quiz_id = request.args.get("quiz_id")
    all_attempts = get_attempts_for_user(user_id, quiz_id)
    serialized = []
    for a in all_attempts:
        serialized.append({
            "id": str(a["id"]),
            "quiz_id": str(a.get("quiz_id", "")),
            "score": a.get("score", 0),
            "total_questions": a.get("total_questions", 0),
            "percentage": a.get("percentage", 0),
            "weak_topics": a.get("weak_topics", []),
            "attempted_at": a.get("attempted_at", ""),
        })
    return jsonify({"attempts": serialized}), 200


@quiz_bp.route("/weak-areas", methods=["GET"])
@login_required
def weak_areas():
    user_id = get_current_user_id()
    subject_id = request.args.get("subject_id")
    agent = WeakAreaAgent()
    result = agent.analyse(user_id, subject_id)
    return jsonify(result), 200

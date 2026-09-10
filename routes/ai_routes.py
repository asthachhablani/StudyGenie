"""
AI routes — ask, summary, flashcards, study-plan, revision, chat history.
"""
import logging
from flask import Blueprint, request, jsonify
from models.auth import login_required, get_current_user_id
from agents.knowledge_agent import KnowledgeAgent
from agents.summary_agent import SummaryAgent
from agents.flashcard_agent import FlashcardAgent
from agents.study_assistant_agent import StudyAssistantAgent
from agents.revision_agent import RevisionAgent
from services.ibm_service import ibm_status
from services.groq_service import groq_status

logger = logging.getLogger(__name__)
ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/ask", methods=["POST"])
@login_required
def ask():
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    subject_id = (data.get("subject_id") or "").strip()

    if not question:
        return jsonify({"error": "Question is required"}), 400

    agent = KnowledgeAgent()
    result = agent.answer(question, subject_id)
    return jsonify(result), 200


@ai_bp.route("/summary", methods=["POST"])
@login_required
def summary():
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}
    topic = (data.get("topic") or "").strip()
    subject_id = (data.get("subject_id") or "").strip()
    summary_type = data.get("summary_type", "detailed")

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    agent = SummaryAgent()
    result = agent.generate(subject_id, topic, summary_type=summary_type)
    return jsonify(result), 200


@ai_bp.route("/flashcards", methods=["POST"])
@login_required
def flashcards():
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}
    topic = (data.get("topic") or "").strip()
    subject_id = (data.get("subject_id") or "").strip()
    count = min(int(data.get("count", 10)), 30)

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    agent = FlashcardAgent()
    result = agent.generate(subject_id, topic, count=count, user_id=user_id)
    return jsonify(result), 200


@ai_bp.route("/revision", methods=["POST"])
@login_required
def revision():
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}
    subject_id = (data.get("subject_id") or "").strip()
    extra_topics = data.get("topics", [])

    agent = RevisionAgent()
    result = agent.generate(user_id, subject_id, extra_topics=extra_topics)
    return jsonify(result), 200


@ai_bp.route("/chat", methods=["POST"])
@login_required
def chat():
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    subject_id = (data.get("subject_id") or "").strip()

    if not message:
        return jsonify({"error": "Message is required"}), 400

    agent = StudyAssistantAgent()
    result = agent.chat(user_id, subject_id, message)
    return jsonify(result), 200


@ai_bp.route("/chat/history", methods=["GET"])
@login_required
def chat_history():
    user_id = get_current_user_id()
    subject_id = request.args.get("subject_id")
    agent = StudyAssistantAgent()
    history = agent.get_history(user_id, subject_id)
    return jsonify({"history": history}), 200


@ai_bp.route("/status", methods=["GET"])
@login_required
def ai_status():
    return jsonify({
        "ibm": ibm_status(),
        "groq": groq_status(),
    }), 200

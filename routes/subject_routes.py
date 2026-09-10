"""
Subject routes.
"""
import logging
from flask import Blueprint, request, jsonify
from models.auth import login_required, get_current_user_id
from models.subject_model import (create_subject, get_subjects_for_user,
                                   get_subject, update_subject,
                                   delete_subject, serialize_subject)
from models.document_model import get_documents_for_user
from models.progress_model import get_progress_for_user

logger = logging.getLogger(__name__)
subject_bp = Blueprint("subjects", __name__)


@subject_bp.route("", methods=["GET"])
@login_required
def list_subjects():
    user_id = get_current_user_id()
    subjects = get_subjects_for_user(user_id)
    return jsonify({"subjects": [serialize_subject(s) for s in subjects]}), 200


@subject_bp.route("", methods=["POST"])
@login_required
def create():
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    if not name:
        return jsonify({"error": "Subject name is required"}), 400
    try:
        subject = create_subject(user_id, name, description)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    return jsonify({"message": "Subject created", "subject": serialize_subject(subject)}), 201


@subject_bp.route("/<subject_id>", methods=["GET"])
@login_required
def get_one(subject_id):
    user_id = get_current_user_id()
    subject = get_subject(subject_id, user_id)
    if not subject:
        return jsonify({"error": "Subject not found"}), 404
    docs = get_documents_for_user(user_id, subject_id)
    from models.document_model import serialize_document
    progress = get_progress_for_user(user_id, subject_id)
    from models.progress_model import serialize_progress
    return jsonify({
        "subject": serialize_subject(subject),
        "documents": [serialize_document(d) for d in docs],
        "progress": [serialize_progress(p) for p in progress],
    }), 200


@subject_bp.route("/<subject_id>", methods=["PUT"])
@login_required
def update(subject_id):
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    if not name:
        return jsonify({"error": "Subject name is required"}), 400
    ok = update_subject(subject_id, user_id, name, description)
    if not ok:
        return jsonify({"error": "Subject not found or no change made"}), 404
    return jsonify({"message": "Subject updated"}), 200


@subject_bp.route("/<subject_id>", methods=["DELETE"])
@login_required
def delete(subject_id):
    user_id = get_current_user_id()
    ok = delete_subject(subject_id, user_id)
    if not ok:
        return jsonify({"error": "Subject not found"}), 404
    return jsonify({"message": "Subject deleted"}), 200

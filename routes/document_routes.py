"""
Document upload and management routes.
"""
import os
import logging
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from models.auth import login_required, get_current_user_id
from models.document_model import (create_document, get_documents_for_user,
                                    get_document, delete_document,
                                    serialize_document, delete_chunks_for_document)
from models.subject_model import get_subject

logger = logging.getLogger(__name__)
document_bp = Blueprint("documents", __name__)


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"


@document_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    user_id = get_current_user_id()

    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    subject_id = request.form.get("subject_id", "").strip()

    if not file or not file.filename:
        return jsonify({"error": "No file selected"}), 400
    if not _allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    if subject_id:
        subject = get_subject(subject_id, user_id)
        if not subject:
            return jsonify({"error": "Subject not found"}), 404

    safe_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_name)
    file.save(file_path)

    try:
        doc = create_document(user_id, subject_id, safe_name, file_path)
    except RuntimeError as exc:
        os.remove(file_path)
        return jsonify({"error": str(exc)}), 503

    return jsonify({
        "message": "File uploaded successfully",
        "document": serialize_document(doc),
    }), 201


@document_bp.route("", methods=["GET"])
@login_required
def list_docs():
    user_id = get_current_user_id()
    subject_id = request.args.get("subject_id")
    docs = get_documents_for_user(user_id, subject_id)
    return jsonify({"documents": [serialize_document(d) for d in docs]}), 200


@document_bp.route("/<doc_id>", methods=["GET"])
@login_required
def get_one(doc_id):
    user_id = get_current_user_id()
    doc = get_document(doc_id, user_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    return jsonify({"document": serialize_document(doc)}), 200


@document_bp.route("/<doc_id>", methods=["DELETE"])
@login_required
def delete(doc_id):
    user_id = get_current_user_id()
    doc = get_document(doc_id, user_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    try:
        if os.path.exists(doc["file_path"]):
            os.remove(doc["file_path"])
        delete_chunks_for_document(doc_id)
        delete_document(doc_id, user_id)
    except Exception as exc:
        logger.error(f"Delete document error: {exc}")
        return jsonify({"error": "Could not fully delete document"}), 500
    return jsonify({"message": "Document deleted"}), 200


@document_bp.route("/<doc_id>/process", methods=["POST"])
@login_required
def process(doc_id):
    user_id = get_current_user_id()
    doc = get_document(doc_id, user_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    if doc.get("status") == "processing":
        return jsonify({"message": "Document is already being processed"}), 200

    # Trigger processing in background thread
    import threading
    from agents.document_agent import DocumentAgent
    agent = DocumentAgent()

    def run():
        try:
            agent.process(doc_id, doc["file_path"], doc.get("subject_id", ""), user_id)
        except Exception as exc:
            logger.error(f"Background processing failed for {doc_id}: {exc}")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    return jsonify({"message": "Document processing started", "document_id": doc_id}), 202

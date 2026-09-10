"""
Authentication routes: register, login, logout, profile.
"""
import re
import logging
from flask import Blueprint, request, jsonify, session
from models.user_model import (create_user, find_user_by_email,
                                find_user_by_id, verify_password,
                                serialize_user)
from models.auth import generate_token, login_required, get_current_user_id

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    confirm = data.get("confirm_password") or ""

    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email address"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if password != confirm:
        return jsonify({"error": "Passwords do not match"}), 400

    if find_user_by_email(email):
        return jsonify({"error": "An account with this email already exists"}), 409

    try:
        user = create_user(name, email, password)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503

    token = generate_token(str(user["id"]), email)
    session["user_id"] = str(user["id"])
    return jsonify({"message": "Registration successful", "token": token,
                    "user": serialize_user(user)}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = find_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = generate_token(str(user["id"]), email)
    session["user_id"] = str(user["id"])
    return jsonify({"message": "Login successful", "token": token,
                    "user": serialize_user(user)}), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    user_id = get_current_user_id()
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": serialize_user(user)}), 200

"""
JWT-based authentication helpers.
"""
import logging
from functools import wraps
from flask import request, jsonify, session
import jwt
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24


def generate_token(user_id: str, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, Config.SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user_id() -> str | None:
    """Extract the authenticated user ID from Authorization header or session."""
    # Try Bearer token first
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = decode_token(token)
        if payload:
            return payload.get("user_id")
    # Fall back to session
    return session.get("user_id")


def login_required(f):
    """Decorator that rejects unauthenticated requests."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Unauthorized", "message": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated

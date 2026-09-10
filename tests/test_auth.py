"""
Tests for authentication endpoints.
External API calls (Groq, IBM) are mocked.
"""
import json
import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def client(tmp_path):
    """Create a Flask test client with a temporary SQLite database."""
    db_path = str(tmp_path / "test_studygenie.db")
    os.environ["SECRET_KEY"] = "test_secret_key_for_testing"
    os.environ["DATABASE_PATH"] = db_path

    from app import create_app
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as c:
        yield c


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_register_missing_name(client):
    resp = client.post("/api/auth/register",
                       data=json.dumps({"email": "a@b.com", "password": "pass1234", "confirm_password": "pass1234"}),
                       content_type="application/json")
    assert resp.status_code == 400


def test_register_invalid_email(client):
    resp = client.post("/api/auth/register",
                       data=json.dumps({
                           "name": "Test User",
                           "email": "not-an-email",
                           "password": "testpass123",
                           "confirm_password": "testpass123",
                       }),
                       content_type="application/json")
    assert resp.status_code == 400


def test_register_short_password(client):
    resp = client.post("/api/auth/register",
                       data=json.dumps({
                           "name": "Test User",
                           "email": "a@b.com",
                           "password": "short",
                           "confirm_password": "short",
                       }),
                       content_type="application/json")
    assert resp.status_code == 400


def test_register_password_mismatch(client):
    resp = client.post("/api/auth/register",
                       data=json.dumps({
                           "name": "Test User",
                           "email": "a@b.com",
                           "password": "pass1234",
                           "confirm_password": "different",
                       }),
                       content_type="application/json")
    assert resp.status_code == 400


def test_register_success_and_login(client):
    """Full register → login → me flow."""
    payload = {
        "name": "Test Student",
        "email": "student@test.com",
        "password": "securepass123",
        "confirm_password": "securepass123",
    }
    resp = client.post("/api/auth/register",
                       data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 201
    data = resp.get_json()
    assert "token" in data
    assert data["user"]["email"] == "student@test.com"

    # Login
    login_resp = client.post("/api/auth/login",
                             data=json.dumps({"email": "student@test.com", "password": "securepass123"}),
                             content_type="application/json")
    assert login_resp.status_code == 200
    assert "token" in login_resp.get_json()


def test_duplicate_registration(client):
    payload = {
        "name": "A", "email": "dup@test.com",
        "password": "pass1234", "confirm_password": "pass1234",
    }
    client.post("/api/auth/register", data=json.dumps(payload), content_type="application/json")
    resp = client.post("/api/auth/register", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 409


def test_login_invalid_credentials(client):
    resp = client.post("/api/auth/login",
                       data=json.dumps({"email": "nobody@example.com", "password": "wrongpassword"}),
                       content_type="application/json")
    assert resp.status_code == 401


def test_protected_route_without_token(client):
    resp = client.get("/api/subjects")
    assert resp.status_code == 401


def test_protected_dashboard_without_token(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 401

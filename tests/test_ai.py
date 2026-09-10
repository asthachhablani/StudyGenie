"""
Tests for AI routes — SQLite version.
"""
import json
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def client(tmp_path):
    db_path = str(tmp_path / "test_ai.db")
    os.environ["SECRET_KEY"] = "test_secret_key"
    os.environ["DATABASE_PATH"] = db_path
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_ask_requires_auth(client):
    resp = client.post("/api/ai/ask",
                       data=json.dumps({"question": "What is paging?"}),
                       content_type="application/json")
    assert resp.status_code == 401


def test_summary_requires_auth(client):
    resp = client.post("/api/ai/summary",
                       data=json.dumps({"topic": "normalization"}),
                       content_type="application/json")
    assert resp.status_code == 401


def test_flashcards_requires_auth(client):
    resp = client.post("/api/ai/flashcards",
                       data=json.dumps({"topic": "normalization"}),
                       content_type="application/json")
    assert resp.status_code == 401


def test_ai_status_requires_auth(client):
    resp = client.get("/api/ai/status")
    assert resp.status_code == 401


def test_chat_requires_auth(client):
    resp = client.post("/api/ai/chat",
                       data=json.dumps({"message": "explain paging"}),
                       content_type="application/json")
    assert resp.status_code == 401

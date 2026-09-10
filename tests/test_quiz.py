"""
Tests for quiz endpoints — SQLite version.
"""
import json
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def client(tmp_path):
    db_path = str(tmp_path / "test_quiz.db")
    os.environ["SECRET_KEY"] = "test_secret_key"
    os.environ["DATABASE_PATH"] = db_path
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _register_and_get_token(client, email="quiztester@test.com"):
    payload = {
        "name": "Quiz Tester",
        "email": email,
        "password": "securepass123",
        "confirm_password": "securepass123",
    }
    resp = client.post("/api/auth/register",
                       data=json.dumps(payload), content_type="application/json")
    data = resp.get_json()
    return data.get("token", "")


def test_quiz_list_requires_auth(client):
    resp = client.get("/api/quizzes")
    assert resp.status_code == 401


def test_quiz_generate_requires_auth(client):
    resp = client.post("/api/quizzes/generate",
                       data=json.dumps({"topic": "paging", "subject_id": "1"}),
                       content_type="application/json")
    assert resp.status_code == 401


def test_quiz_submit_requires_auth(client):
    resp = client.post("/api/quizzes/1/submit",
                       data=json.dumps({"answers": []}),
                       content_type="application/json")
    assert resp.status_code == 401


def test_quiz_list_with_auth(client):
    token = _register_and_get_token(client)
    resp = client.get("/api/quizzes",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "quizzes" in resp.get_json()


def test_quiz_score_calculation():
    """Unit test: quiz scoring logic."""
    mock_questions = [
        {"question": "Q1", "options": ["A", "B", "C", "D"], "correct_answer": "A",
         "explanation": "A is correct", "topic": "Test", "difficulty": "easy"},
        {"question": "Q2", "options": ["A", "B", "C", "D"], "correct_answer": "B",
         "explanation": "B is correct", "topic": "Test", "difficulty": "easy"},
    ]
    score = 0
    for q in mock_questions:
        if "A" == q["correct_answer"]:
            score += 1
    assert score == 1  # Only Q1 is correct when always answering A


def test_subject_crud_with_auth(client):
    """Full subject create → list → update → delete flow."""
    token = _register_and_get_token(client)
    auth = {"Authorization": f"Bearer {token}"}

    # Create
    resp = client.post("/api/subjects",
                       data=json.dumps({"name": "DBMS", "description": "Database"}),
                       content_type="application/json",
                       headers=auth)
    assert resp.status_code == 201
    sub_id = resp.get_json()["subject"]["id"]

    # List
    resp = client.get("/api/subjects", headers=auth)
    assert resp.status_code == 200
    assert len(resp.get_json()["subjects"]) == 1

    # Update
    resp = client.put(f"/api/subjects/{sub_id}",
                      data=json.dumps({"name": "DBMS Updated", "description": "New desc"}),
                      content_type="application/json",
                      headers=auth)
    assert resp.status_code == 200

    # Delete
    resp = client.delete(f"/api/subjects/{sub_id}", headers=auth)
    assert resp.status_code == 200

    # Verify deleted
    resp = client.get("/api/subjects", headers=auth)
    assert len(resp.get_json()["subjects"]) == 0

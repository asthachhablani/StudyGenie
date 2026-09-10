"""
Tests for document upload validation — SQLite version.
"""
import io
import json
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def client(tmp_path):
    db_path = str(tmp_path / "test_docs.db")
    os.environ["SECRET_KEY"] = "test_secret_key"
    os.environ["DATABASE_PATH"] = db_path
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_upload_without_auth(client):
    data = {"file": (io.BytesIO(b"fake pdf content"), "test.pdf")}
    resp = client.post("/api/documents/upload",
                       data=data,
                       content_type="multipart/form-data")
    assert resp.status_code == 401


def test_list_documents_requires_auth(client):
    resp = client.get("/api/documents")
    assert resp.status_code == 401


def test_delete_document_requires_auth(client):
    resp = client.delete("/api/documents/1")
    assert resp.status_code == 401

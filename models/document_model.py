"""
Document model — SQLite CRUD helpers for the documents table.
"""
import logging
from models.db import get_db_connection

logger = logging.getLogger(__name__)


def create_document(user_id, subject_id, filename: str, file_path: str) -> dict:
    conn = get_db_connection()
    try:
        cur = conn.execute(
            """INSERT INTO documents (user_id, subject_id, filename, file_path)
               VALUES (?, ?, ?, ?)""",
            (int(user_id), int(subject_id) if subject_id else 0, filename, file_path),
        )
        conn.commit()
        doc_id = cur.lastrowid
    finally:
        conn.close()
    return get_document(doc_id, user_id)


def get_documents_for_user(user_id, subject_id=None) -> list:
    conn = get_db_connection()
    try:
        if subject_id:
            rows = conn.execute(
                "SELECT * FROM documents WHERE user_id = ? AND subject_id = ? ORDER BY uploaded_at DESC",
                (int(user_id), int(subject_id)),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC",
                (int(user_id),),
            ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def get_document(doc_id, user_id) -> dict | None:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ? AND user_id = ?",
            (int(doc_id), int(user_id)),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def update_document_status(doc_id, status: str, extra: dict = None):
    conn = get_db_connection()
    try:
        if status == "processed":
            page_count = (extra or {}).get("page_count", 0)
            chunk_count = (extra or {}).get("chunk_count", 0)
            conn.execute(
                """UPDATE documents
                   SET status = ?, processed_at = CURRENT_TIMESTAMP,
                       page_count = ?, chunk_count = ?
                   WHERE id = ?""",
                (status, page_count, chunk_count, int(doc_id)),
            )
        elif extra and "error" in extra:
            conn.execute(
                "UPDATE documents SET status = ? WHERE id = ?",
                (status, int(doc_id)),
            )
        else:
            conn.execute(
                "UPDATE documents SET status = ? WHERE id = ?",
                (status, int(doc_id)),
            )
        conn.commit()
    finally:
        conn.close()


def delete_document(doc_id, user_id) -> bool:
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "DELETE FROM documents WHERE id = ? AND user_id = ?",
            (int(doc_id), int(user_id)),
        )
        conn.commit()
    finally:
        conn.close()
    return cur.rowcount > 0


# ── Chunk helpers (stored in ChromaDB — these are lightweight metadata only) ──

def save_chunks(chunks: list):
    """
    Chunks are indexed in ChromaDB (vector store).
    This function is a no-op for the SQLite layer; metadata is updated
    via update_document_status instead.
    """
    pass


def get_chunks_for_document(doc_id) -> list:
    """Chunks live in ChromaDB. Return empty list from SQL layer."""
    return []


def get_chunks_for_subject(subject_id) -> list:
    """Chunks live in ChromaDB. Return empty list from SQL layer."""
    return []


def delete_chunks_for_document(doc_id):
    """Chunks are removed from ChromaDB by the document agent."""
    pass


def serialize_document(d: dict) -> dict:
    return {
        "id": str(d["id"]),
        "user_id": str(d.get("user_id", "")),
        "subject_id": str(d.get("subject_id", "")),
        "filename": d.get("filename", ""),
        "status": d.get("status", ""),
        "uploaded_at": d.get("uploaded_at", ""),
        "processed_at": d.get("processed_at"),
        "page_count": d.get("page_count", 0),
        "chunk_count": d.get("chunk_count", 0),
    }

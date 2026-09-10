"""
Flashcard Agent — generates question/answer flashcards from study material.
"""
import json
import logging
from services.rag_service import build_rag_context
from services.groq_service import generate_flashcards
from models.db import get_db_connection

logger = logging.getLogger(__name__)


class FlashcardAgent:
    def generate(self, subject_id: str, topic: str, count: int = 10,
                 user_id: str = None) -> dict:
        logger.info(f"[FlashcardAgent] topic='{topic}' count={count}")

        rag = build_rag_context(subject_id, topic, top_k=8)
        context_text = rag.get("context_text", "")

        if not context_text:
            return {
                "flashcards": [],
                "message": "No study material found. Upload documents first.",
                "sources": [],
            }

        cards = generate_flashcards(topic, context_text, count=count)

        if not cards:
            return {
                "flashcards": [],
                "message": "Flashcard generation failed. Check AI configuration.",
                "sources": rag.get("sources", []),
            }

        # Persist individual flashcard rows to SQLite
        if user_id:
            try:
                conn = get_db_connection()
                try:
                    for card in cards:
                        conn.execute(
                            """INSERT INTO flashcards
                               (user_id, subject_id, topic, question, answer, difficulty)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (
                                int(user_id),
                                int(subject_id) if subject_id else 0,
                                topic,
                                card.get("question", ""),
                                card.get("answer", ""),
                                card.get("difficulty", "medium"),
                            ),
                        )
                    conn.commit()
                finally:
                    conn.close()
            except Exception as exc:
                logger.warning(f"Flashcard persistence error: {exc}")

        return {
            "flashcards": cards,
            "count": len(cards),
            "sources": rag.get("sources", []),
        }

    def get_saved(self, user_id: str, subject_id: str = None) -> list:
        conn = get_db_connection()
        try:
            if subject_id:
                rows = conn.execute(
                    """SELECT topic, question, answer, difficulty, created_at
                       FROM flashcards WHERE user_id = ? AND subject_id = ?
                       ORDER BY created_at DESC LIMIT 100""",
                    (int(user_id), int(subject_id)),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT topic, question, answer, difficulty, created_at
                       FROM flashcards WHERE user_id = ?
                       ORDER BY created_at DESC LIMIT 100""",
                    (int(user_id),),
                ).fetchall()
        finally:
            conn.close()

        # Group by topic
        by_topic: dict = {}
        for r in rows:
            t = r["topic"] or "General"
            by_topic.setdefault(t, []).append({
                "question": r["question"],
                "answer": r["answer"],
                "difficulty": r["difficulty"],
            })

        return [
            {"topic": t, "flashcards": cards, "created_at": ""}
            for t, cards in by_topic.items()
        ]

"""
Study Assistant Agent — the conversational entry point.
Routes student requests to the appropriate specialized agent.
"""
import logging
import re
from agents.knowledge_agent import KnowledgeAgent
from agents.summary_agent import SummaryAgent
from agents.flashcard_agent import FlashcardAgent
from agents.quiz_agent import QuizAgent
from agents.revision_agent import RevisionAgent
from agents.weak_area_agent import WeakAreaAgent
from models.db import get_db_connection

logger = logging.getLogger(__name__)

# Intent detection patterns
_INTENT_PATTERNS = {
    "summary": [r"\bsummar", r"\bkey points\b", r"\bimportant topics\b", r"\bbrief\b"],
    "flashcard": [r"\bflashcard", r"\bcard", r"\bq&a\b", r"\bquestion.?answer"],
    "quiz": [r"\bquiz\b", r"\btest me\b", r"\bmcq\b", r"\bpractice questions\b"],
    "revision": [r"\brevise\b", r"\brevision\b", r"\bweak\b", r"\bwhat should i study"],
    "plan": [r"\bstudy plan\b", r"\bschedule\b", r"\bplan\b"],
    "weakness": [r"\bweak area\b", r"\bwhere am i weak\b", r"\bperformance\b"],
}


def _detect_intent(message: str) -> str:
    lower = message.lower()
    for intent, patterns in _INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, lower):
                return intent
    return "answer"  # default to RAG Q&A


class StudyAssistantAgent:

    def chat(self, user_id: str, subject_id: str, message: str) -> dict:
        intent = _detect_intent(message)
        logger.info(f"[StudyAssistant] user_id={user_id} intent={intent}")

        result = {}

        if intent == "summary":
            agent = SummaryAgent()
            result = agent.generate(subject_id, message, summary_type="key_points")
            result["intent"] = "summary"

        elif intent == "flashcard":
            agent = FlashcardAgent()
            result = agent.generate(subject_id, message, count=8, user_id=user_id)
            result["intent"] = "flashcard"

        elif intent == "quiz":
            agent = QuizAgent()
            result = agent.generate(user_id, subject_id, message, count=5)
            result["intent"] = "quiz"

        elif intent == "revision":
            agent = RevisionAgent()
            result = agent.generate(user_id, subject_id)
            result["intent"] = "revision"

        elif intent == "plan":
            from agents.study_planner_agent import StudyPlannerAgent
            agent = StudyPlannerAgent()
            result = agent.create_plan(user_id, subject_id, hours_per_day=2, duration_days=7)
            result["intent"] = "plan"

        elif intent == "weakness":
            agent = WeakAreaAgent()
            result = agent.analyse(user_id, subject_id)
            result["intent"] = "weakness"

        else:
            agent = KnowledgeAgent()
            result = agent.answer(message, subject_id)
            result["intent"] = "answer"

        # Store in chat history
        self._save_chat(user_id, subject_id, message, intent)
        return result

    def get_history(self, user_id: str, subject_id: str = None, limit: int = 20) -> list:
        conn = get_db_connection()
        try:
            if subject_id:
                rows = conn.execute(
                    """SELECT id, question, intent, created_at
                       FROM chat_history WHERE user_id = ? AND subject_id = ?
                       ORDER BY created_at DESC LIMIT ?""",
                    (int(user_id), int(subject_id) if subject_id else 0, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT id, question, intent, created_at
                       FROM chat_history WHERE user_id = ?
                       ORDER BY created_at DESC LIMIT ?""",
                    (int(user_id), limit),
                ).fetchall()
        finally:
            conn.close()
        return [
            {
                "id": str(r["id"]),
                "question": r["question"],
                "intent": r["intent"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    def _save_chat(self, user_id: str, subject_id: str, question: str, intent: str):
        conn = get_db_connection()
        try:
            conn.execute(
                """INSERT INTO chat_history (user_id, subject_id, question, intent)
                   VALUES (?, ?, ?, ?)""",
                (
                    int(user_id),
                    int(subject_id) if subject_id else 0,
                    question[:500],
                    intent,
                ),
            )
            conn.commit()
        except Exception as exc:
            logger.warning(f"Chat history save error: {exc}")
        finally:
            conn.close()

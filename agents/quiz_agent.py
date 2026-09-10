"""
Quiz Agent — generates, stores and scores MCQ quizzes.
"""
import logging
from services.rag_service import build_rag_context
from services.groq_service import generate_quiz as groq_generate_quiz
from models.quiz_model import create_quiz, get_quiz, save_quiz_attempt
from models.progress_model import upsert_topic_progress

logger = logging.getLogger(__name__)


class QuizAgent:

    def generate(self, user_id: str, subject_id: str, topic: str,
                 count: int = 10, difficulty: str = "medium") -> dict:
        logger.info(f"[QuizAgent] Generating quiz topic='{topic}' count={count}")

        rag = build_rag_context(subject_id, topic, top_k=10)
        context_text = rag.get("context_text", "")

        if not context_text:
            return {
                "error": "No study material found. Upload and process documents first.",
                "quiz": None,
            }

        questions = groq_generate_quiz(topic, context_text, count=count, difficulty=difficulty)

        if not questions:
            return {
                "error": "Quiz generation failed. Check Groq API configuration.",
                "quiz": None,
            }

        quiz = create_quiz(user_id, subject_id, topic, questions)
        return {
            "quiz": {
                "id": str(quiz["_id"]),
                "topic": quiz["topic"],
                "question_count": len(questions),
                "questions": [
                    {
                        "question": q.get("question", ""),
                        "options": q.get("options", []),
                        "topic": q.get("topic", topic),
                        "difficulty": q.get("difficulty", difficulty),
                    }
                    for q in questions
                ],
            }
        }

    def score(self, user_id: str, quiz_id: str, submitted_answers: list) -> dict:
        """
        submitted_answers: list of {"question_index": int, "selected": "A"}
        Returns detailed scoring result.
        """
        quiz = get_quiz(quiz_id, user_id)
        if not quiz:
            return {"error": "Quiz not found"}

        questions = quiz.get("questions", [])
        score = 0
        total = len(questions)
        detailed = []
        topic_scores: dict = {}
        topic_totals: dict = {}

        for i, q in enumerate(questions):
            correct = q.get("correct_answer", "").strip().upper()
            # Find submitted answer for this index
            submitted = ""
            for sa in submitted_answers:
                if str(sa.get("question_index")) == str(i):
                    submitted = (sa.get("selected") or "").strip().upper()
                    break

            is_correct = submitted == correct
            if is_correct:
                score += 1

            topic = q.get("topic", quiz.get("topic", "General"))
            topic_totals[topic] = topic_totals.get(topic, 0) + 1
            if is_correct:
                topic_scores[topic] = topic_scores.get(topic, 0) + 1

            detailed.append({
                "question_index": i,
                "question": q.get("question", ""),
                "options": q.get("options", []),
                "submitted": submitted,
                "correct_answer": correct,
                "is_correct": is_correct,
                "explanation": q.get("explanation", ""),
                "topic": topic,
            })

        # Topic performance
        topic_performance = {}
        weak_topics = []
        strong_topics = []
        for topic, t_total in topic_totals.items():
            t_score = topic_scores.get(topic, 0)
            pct = round(t_score / t_total * 100, 1) if t_total else 0
            topic_performance[topic] = {"score": t_score, "total": t_total, "percentage": pct}
            strength = "strong" if pct >= 70 else ("moderate" if pct >= 50 else "weak")
            if strength == "weak":
                weak_topics.append(topic)
            elif strength == "strong":
                strong_topics.append(topic)
            # Update progress
            upsert_topic_progress(user_id, quiz.get("subject_id", ""), topic, pct, strength)

        percentage = round(score / total * 100, 1) if total else 0
        attempt = save_quiz_attempt(user_id, quiz_id, score, total, detailed, weak_topics)

        return {
            "attempt_id": str(attempt["_id"]),
            "score": score,
            "total": total,
            "percentage": percentage,
            "detailed": detailed,
            "topic_performance": topic_performance,
            "weak_topics": weak_topics,
            "strong_topics": strong_topics,
        }

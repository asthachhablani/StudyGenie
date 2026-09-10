"""
Weak Area Analysis Agent — analyses quiz history to identify weak topics.
"""
import logging
from models.quiz_model import get_attempts_for_user
from models.progress_model import get_progress_for_user, get_weak_topics, get_strong_topics

logger = logging.getLogger(__name__)


class WeakAreaAgent:

    def analyse(self, user_id: str, subject_id: str = None) -> dict:
        logger.info(f"[WeakAreaAgent] user_id={user_id} subject_id={subject_id}")

        progress = get_progress_for_user(user_id, subject_id)
        weak = get_weak_topics(user_id, subject_id, threshold=50.0)
        strong = get_strong_topics(user_id, subject_id, threshold=70.0)

        # Recent attempts
        attempts = get_attempts_for_user(user_id)[:10]
        repeated_mistakes = {}
        for attempt in attempts:
            for detail in attempt.get("answers", []):
                if not detail.get("is_correct"):
                    topic = detail.get("topic", "General")
                    repeated_mistakes[topic] = repeated_mistakes.get(topic, 0) + 1

        # Sort by frequency
        sorted_mistakes = sorted(repeated_mistakes.items(), key=lambda x: x[1], reverse=True)[:5]

        recommendations = []
        if weak:
            recommendations.append(
                f"Focus on revising: {', '.join(weak[:3])} before your next attempt."
            )
        if sorted_mistakes:
            top_mistake = sorted_mistakes[0][0]
            recommendations.append(
                f"You have repeatedly made mistakes on '{top_mistake}'. "
                "Consider generating a quiz specifically on this topic."
            )
        if not weak and not repeated_mistakes:
            recommendations.append(
                "Great performance! Keep practising to maintain your strong understanding."
            )

        return {
            "weak_topics": weak,
            "strong_topics": strong,
            "repeated_mistakes": [{"topic": t, "count": c} for t, c in sorted_mistakes],
            "recommendations": recommendations,
            "progress_count": len(progress),
        }

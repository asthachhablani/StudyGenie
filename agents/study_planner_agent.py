"""
Study Planner Agent — generates a personalized day-by-day study plan.
"""
import logging
from models.subject_model import get_subjects_for_user
from models.progress_model import get_weak_topics
from models.study_plan_model import create_study_plan, serialize_plan
from services.groq_service import generate_study_plan

logger = logging.getLogger(__name__)


class StudyPlannerAgent:

    def create_plan(self, user_id: str, subject_id: str,
                    hours_per_day: float, duration_days: int,
                    exam_date: str = None) -> dict:
        logger.info(f"[StudyPlannerAgent] user_id={user_id} duration={duration_days}")

        # Get subject name
        from models.subject_model import get_subject
        subject = get_subject(subject_id, user_id) if subject_id else None
        subject_name = subject["name"] if subject else "All Subjects"

        # Get weak topics for this user/subject
        weak = get_weak_topics(user_id, subject_id, threshold=60.0)

        subjects_list = [subject_name] if subject_name != "All Subjects" else [
            s["name"] for s in get_subjects_for_user(user_id)
        ]

        tasks_data = generate_study_plan(
            subjects=subjects_list,
            weak_topics=weak,
            hours_per_day=hours_per_day,
            duration_days=duration_days,
            exam_date=exam_date,
        )

        if not tasks_data:
            return {
                "error": "Study plan generation failed. Check AI configuration.",
                "plan": None,
            }

        plan = create_study_plan(
            user_id=user_id,
            subject_id=subject_id or "",
            tasks=tasks_data,
            duration_days=duration_days,
            exam_date=exam_date,
        )

        return {"plan": serialize_plan(plan)}

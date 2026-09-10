"""
Revision Agent — generates targeted revision material based on weak areas.
"""
import logging
from services.rag_service import build_rag_context
from services.groq_service import generate_revision_material
from models.progress_model import get_weak_topics

logger = logging.getLogger(__name__)


class RevisionAgent:

    def generate(self, user_id: str, subject_id: str, extra_topics: list = None) -> dict:
        logger.info(f"[RevisionAgent] user_id={user_id} subject_id={subject_id}")

        weak = get_weak_topics(user_id, subject_id, threshold=60.0)
        if extra_topics:
            weak = list(set(weak + extra_topics))

        if not weak:
            return {
                "revision": (
                    "No weak topics identified yet. Attempt some quizzes first to "
                    "identify areas that need revision."
                ),
                "weak_topics": [],
                "sources": [],
            }

        # Build context for weak topics
        combined_context = ""
        all_sources = []
        for topic in weak[:4]:  # Limit to top 4 weak topics
            rag = build_rag_context(subject_id, topic, top_k=4)
            context = rag.get("context_text", "")
            if context:
                combined_context += f"\n\n### {topic}\n{context}"
                all_sources.extend(rag.get("sources", []))

        if not combined_context:
            return {
                "revision": (
                    "No study material found for your weak topics. "
                    "Upload your study documents first."
                ),
                "weak_topics": weak,
                "sources": [],
            }

        revision_text = generate_revision_material(weak, combined_context)

        if not revision_text:
            revision_text = "Revision material generation failed. Check AI configuration."

        return {
            "revision": revision_text,
            "weak_topics": weak,
            "sources": all_sources,
        }

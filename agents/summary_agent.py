"""
Summary Agent — generates various types of summaries from study material.
"""
import logging
from services.rag_service import build_rag_context
from services.groq_service import generate_summary
from services.ibm_service import generate_with_ibm, ibm_status

logger = logging.getLogger(__name__)

SUMMARY_TYPES = ["short", "detailed", "key_points", "exam", "definitions"]


class SummaryAgent:
    def generate(self, subject_id: str, topic: str, summary_type: str = "detailed",
                 top_k: int = 8) -> dict:
        logger.info(f"[SummaryAgent] topic='{topic}' type='{summary_type}'")

        rag = build_rag_context(subject_id, topic, top_k=top_k)
        context_text = rag.get("context_text", "")

        if not context_text:
            return {
                "summary": (
                    "No study material found for this subject. "
                    "Please upload and process your study documents first."
                ),
                "sources": [],
                "model_used": "none",
            }

        summary = generate_summary(topic, context_text, summary_type=summary_type)

        model_used = "groq"
        if not summary and ibm_status()["configured"]:
            prompt = (
                f"Summarize the following study material on '{topic}' "
                f"({summary_type} style):\n\n{context_text}"
            )
            summary = generate_with_ibm(prompt, max_tokens=1500)
            model_used = "ibm_granite"

        if not summary:
            summary = "Summary generation failed. Please try again or check your AI configuration."
            model_used = "none"

        return {
            "summary": summary,
            "sources": rag.get("sources", []),
            "model_used": model_used,
        }

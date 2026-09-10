"""
Knowledge / RAG Agent — answers student questions using retrieved context.
Prefers IBM model where configured, falls back to Groq.
"""
import logging
from services.rag_service import build_rag_context, format_rag_prompt
from services.ibm_service import generate_with_ibm, ibm_status
from services.groq_service import generate_answer_with_context

logger = logging.getLogger(__name__)


class KnowledgeAgent:
    """Retrieves relevant context and generates an answer."""

    def answer(self, question: str, subject_id: str) -> dict:
        logger.info(f"[KnowledgeAgent] question='{question[:60]}...' subject_id={subject_id}")

        # Retrieve context
        rag = build_rag_context(subject_id, question)
        context_text = rag.get("context_text", "")
        sources = rag.get("sources", [])

        if not context_text:
            return {
                "answer": (
                    "I could not find relevant information in your uploaded study material. "
                    "Please upload study documents for this subject first."
                ),
                "sources": [],
                "model_used": "none",
            }

        # Choose model
        answer_text = None
        model_used = "none"

        # Try IBM first
        if ibm_status()["configured"]:
            prompt = format_rag_prompt(question, context_text)
            answer_text = generate_with_ibm(prompt, max_tokens=1024)
            if answer_text:
                model_used = "ibm_granite"

        # Fall back to Groq
        if not answer_text:
            answer_text = generate_answer_with_context(question, context_text)
            if answer_text:
                model_used = "groq"

        if not answer_text:
            answer_text = (
                "AI service is currently unavailable. "
                "Please check your API configuration."
            )

        return {
            "answer": answer_text,
            "sources": sources,
            "model_used": model_used,
        }

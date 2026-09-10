"""
RAG Service — full retrieval-augmented generation pipeline.
"""
import logging
from typing import List, Dict
from services.embedding_service import embed_query
from services.vector_service import similarity_search
from config import Config

logger = logging.getLogger(__name__)


def build_rag_context(subject_id: str, question: str, top_k: int = None) -> Dict:
    """
    Retrieve relevant chunks for a question from the vector store.
    Returns: {chunks, context_text, sources}
    """
    k = top_k or Config.TOP_K_RESULTS
    query_emb = embed_query(question)
    if not query_emb:
        return {"chunks": [], "context_text": "", "sources": []}

    chunks = similarity_search(subject_id, query_emb, top_k=k)
    if not chunks:
        return {"chunks": [], "context_text": "", "sources": []}

    context_parts = []
    sources = []
    seen_sources = set()

    for chunk in chunks:
        context_parts.append(chunk["text"])
        meta = chunk.get("metadata", {})
        source_key = f"{meta.get('filename', 'Unknown')}:p{meta.get('page_number', '?')}"
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            sources.append({
                "filename": meta.get("filename", "Unknown"),
                "page_number": meta.get("page_number", "?"),
                "document_id": meta.get("document_id", ""),
            })

    return {
        "chunks": chunks,
        "context_text": "\n\n".join(context_parts),
        "sources": sources,
    }


def format_rag_prompt(question: str, context_text: str) -> str:
    if not context_text:
        return (
            f"The student asked: '{question}'\n\n"
            "There is no study material available for this subject yet. "
            "Kindly ask the student to upload their study documents first."
        )
    return (
        "You are StudyGenie AI, a personalized study assistant. "
        "Answer the student's question using ONLY the provided study material context below. "
        "If the answer is not found in the context, say clearly: "
        "'I could not find this information in your uploaded study material.'\n\n"
        f"STUDY MATERIAL CONTEXT:\n{context_text}\n\n"
        f"STUDENT QUESTION: {question}\n\n"
        "Provide a clear, educational answer with:\n"
        "1. Simple explanation\n"
        "2. Key concepts\n"
        "3. Example (if relevant)\n"
        "4. Important points to remember"
    )

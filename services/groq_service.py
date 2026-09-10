"""
Groq Service — fast LLM inference via Groq API.
All credentials read from environment variables.
"""
import logging
import json
import re
from typing import List, Dict
from config import Config

logger = logging.getLogger(__name__)

_groq_client = None


def _get_groq_client():
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    if not Config.groq_configured():
        logger.warning("Groq API key not configured.")
        return None
    try:
        from groq import Groq
        _groq_client = Groq(api_key=Config.GROQ_API_KEY)
        logger.info("Groq client initialized.")
    except Exception as exc:
        logger.error(f"Groq initialization error: {exc}")
        _groq_client = None
    return _groq_client


def _chat(messages: list, max_tokens: int = 2048, temperature: float = 0.7) -> str | None:
    client = _get_groq_client()
    if client is None:
        return None
    try:
        resp = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.error(f"Groq API error: {exc}")
        return None


def generate_text(prompt: str, system: str = None, max_tokens: int = 1024) -> str | None:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return _chat(messages, max_tokens=max_tokens)


def generate_summary(topic: str, context: str, summary_type: str = "detailed") -> str | None:
    type_instructions = {
        "short": "Write a concise 3-5 sentence summary highlighting the most important points.",
        "detailed": "Write a comprehensive summary covering all major concepts, definitions, and examples.",
        "key_points": "List 8-12 key bullet points covering the most important concepts.",
        "exam": "List the most exam-important topics, likely questions, and key definitions students must memorize.",
        "definitions": "Extract and explain all key definitions and terms.",
    }
    instruction = type_instructions.get(summary_type, type_instructions["detailed"])

    system = (
        "You are StudyGenie AI, an expert educational assistant. "
        "Generate summaries strictly based on the provided study material. "
        "Do not invent information not present in the context. "
        "Use clear, student-friendly language."
    )
    prompt = (
        f"Topic: {topic}\n\n"
        f"Study Material:\n{context}\n\n"
        f"Task: {instruction}"
    )
    return generate_text(prompt, system=system, max_tokens=1500)


def generate_flashcards(topic: str, context: str, count: int = 10) -> list | None:
    system = (
        "You are StudyGenie AI. Generate educational flashcards based strictly on the provided material. "
        "Return ONLY a valid JSON array. No explanation outside the JSON."
    )
    prompt = (
        f"Topic: {topic}\n\n"
        f"Study Material:\n{context}\n\n"
        f"Generate {count} flashcards as a JSON array. Each object must have:\n"
        '{"question": "...", "answer": "...", "topic": "...", "difficulty": "easy|medium|hard"}'
    )
    result = generate_text(prompt, system=system, max_tokens=3000)
    if not result:
        return None
    return _parse_json_list(result)


def generate_quiz(topic: str, context: str, count: int = 10,
                   difficulty: str = "medium") -> list | None:
    system = (
        "You are StudyGenie AI. Generate MCQ quiz questions based strictly on the provided study material. "
        "Return ONLY a valid JSON array. No explanation outside the JSON."
    )
    prompt = (
        f"Topic: {topic}\n"
        f"Difficulty: {difficulty}\n\n"
        f"Study Material:\n{context}\n\n"
        f"Generate {count} MCQ questions as a JSON array. Each object must have:\n"
        '{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], '
        '"correct_answer": "A", "explanation": "...", "topic": "...", "difficulty": "..."}'
        "\n\nIMPORTANT: correct_answer must be the letter only (A, B, C, or D)."
    )
    result = generate_text(prompt, system=system, max_tokens=4000, temperature=0.5)
    if not result:
        return None
    return _parse_json_list(result)


def generate_study_plan(subjects: List[str], weak_topics: List[str],
                         hours_per_day: float, duration_days: int,
                         exam_date: str = None) -> list | None:
    system = (
        "You are StudyGenie AI. Create a personalized day-by-day study plan. "
        "Return ONLY a valid JSON array. No explanation outside the JSON."
    )
    prompt = (
        f"Subjects: {', '.join(subjects)}\n"
        f"Weak Topics (prioritize): {', '.join(weak_topics) or 'None identified yet'}\n"
        f"Available study hours per day: {hours_per_day}\n"
        f"Duration: {duration_days} days\n"
        f"Exam date: {exam_date or 'Not specified'}\n\n"
        f"Create a {duration_days}-day study plan as a JSON array. Each element represents one day:\n"
        '{"day": 1, "date": "Day 1", "tasks": ['
        '{"subject": "...", "topic": "...", "duration_minutes": 60, "activity": "...", "completed": false}'
        ']}'
        "\n\nPrioritize weak topics. Mix subjects across days. Keep tasks realistic."
    )
    result = generate_text(prompt, system=system, max_tokens=4000, temperature=0.4)
    if not result:
        return None
    return _parse_json_list(result)


def generate_revision_material(weak_topics: List[str], context: str) -> str | None:
    system = "You are StudyGenie AI. Generate focused revision material for a student."
    prompt = (
        f"Weak Topics to revise: {', '.join(weak_topics)}\n\n"
        f"Available Study Material:\n{context}\n\n"
        "Generate revision material including:\n"
        "1. Quick notes for each weak topic\n"
        "2. Key definitions\n"
        "3. Common exam questions with brief answers\n"
        "4. Memory tips\n"
        "Keep it concise and exam-focused."
    )
    return generate_text(prompt, system=system, max_tokens=2000)


def generate_answer_with_context(question: str, context: str) -> str | None:
    system = (
        "You are StudyGenie AI, a helpful study assistant. "
        "Answer based on the provided context. If the context doesn't contain the answer, "
        "say so clearly."
    )
    prompt = (
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Provide a clear, educational answer."
    )
    return generate_text(prompt, system=system, max_tokens=1200)


def groq_status() -> dict:
    return {
        "configured": Config.groq_configured(),
        "model": Config.GROQ_MODEL,
    }


def _parse_json_list(text: str) -> list | None:
    """Extract and parse a JSON array from a model response."""
    try:
        # Try direct parse
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to find JSON array within the text
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    logger.warning(f"Could not parse JSON from model response.")
    return None

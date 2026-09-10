"""
PDF Service — extract and clean text from PDF files using PyMuPDF.
"""
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> List[Dict]:
    """
    Extract text from each page of a PDF.
    Returns a list of dicts: {page_number, text}
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF not installed. Run: pip install PyMuPDF")
        return []

    pages = []
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text and text.strip():
                pages.append({"page_number": page_num + 1, "text": text})
        doc.close()
    except Exception as exc:
        logger.error(f"PDF extraction error for {file_path}: {exc}")
    return pages


def clean_text(text: str) -> str:
    """Remove excessive whitespace, fix common OCR artifacts."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = text.strip()
    return text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into chunks of roughly chunk_size words with overlap.
    Splits on sentence boundaries where possible.
    """
    sentences = re.split(r"(?<=[.?!])\s+", text)
    chunks = []
    current_words: List[str] = []
    current_len = 0
    overlap_buffer: List[str] = []

    for sentence in sentences:
        words = sentence.split()
        if not words:
            continue
        if current_len + len(words) > chunk_size and current_words:
            chunk_text_str = " ".join(current_words)
            chunks.append(chunk_text_str)
            # Keep overlap words from end of current chunk
            overlap_buffer = current_words[-overlap:]
            current_words = overlap_buffer + words
            current_len = len(current_words)
        else:
            current_words.extend(words)
            current_len += len(words)

    if current_words:
        chunks.append(" ".join(current_words))

    return [c for c in chunks if len(c.strip()) > 20]


def extract_and_chunk(file_path: str, chunk_size: int = 500,
                      overlap: int = 50) -> Dict:
    """
    Full pipeline: extract pages → clean text → chunk.
    Returns: {pages: [...], chunks: [...], page_count: int, text: str}
    """
    pages = extract_text_from_pdf(file_path)
    if not pages:
        return {"pages": [], "chunks": [], "page_count": 0, "text": ""}

    all_chunks = []
    full_text_parts = []

    for page in pages:
        cleaned = clean_text(page["text"])
        if not cleaned:
            continue
        full_text_parts.append(cleaned)
        page_chunks = chunk_text(cleaned, chunk_size, overlap)
        for idx, chunk in enumerate(page_chunks):
            all_chunks.append({
                "text": chunk,
                "page_number": page["page_number"],
                "chunk_index": idx,
            })

    return {
        "pages": pages,
        "chunks": all_chunks,
        "page_count": len(pages),
        "text": "\n\n".join(full_text_parts),
    }

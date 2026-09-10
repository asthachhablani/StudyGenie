"""
Embedding Service — generate text embeddings using sentence-transformers.
Falls back gracefully if the model is not available.
"""
import logging
from typing import List

logger = logging.getLogger(__name__)

_model = None
_model_name = "all-MiniLM-L6-v2"


def _get_model():
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_model_name)
        logger.info(f"Embedding model '{_model_name}' loaded.")
    except Exception as exc:
        logger.error(f"Failed to load embedding model: {exc}")
        _model = None
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts. Returns list of float vectors."""
    model = _get_model()
    if model is None:
        logger.warning("Embedding model unavailable; returning empty embeddings.")
        return [[] for _ in texts]
    try:
        embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return embeddings.tolist()
    except Exception as exc:
        logger.error(f"Embedding generation error: {exc}")
        return [[] for _ in texts]


def embed_query(query: str) -> List[float]:
    """Generate a single query embedding."""
    results = embed_texts([query])
    return results[0] if results else []

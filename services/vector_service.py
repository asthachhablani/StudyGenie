"""
Vector Service — ChromaDB-backed vector store management.
Each subject gets its own ChromaDB collection.
"""
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

_chroma_client = None


def _get_client():
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client
    try:
        import chromadb
        from config import Config
        persist_dir = Config.VECTOR_STORE_PATH
        os.makedirs(persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
        logger.info(f"ChromaDB initialized at {persist_dir}")
    except Exception as exc:
        logger.error(f"ChromaDB initialization failed: {exc}")
        _chroma_client = None
    return _chroma_client


def _collection_name(subject_id: str) -> str:
    return f"subject_{subject_id}" if subject_id else "default_collection"


def get_or_create_collection(subject_id: str):
    client = _get_client()
    if client is None:
        return None
    name = _collection_name(subject_id)
    try:
        return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
    except Exception as exc:
        logger.error(f"Collection error for {name}: {exc}")
        return None


def add_chunks_to_vector_store(subject_id: str, chunks: List[Dict],
                                embeddings: List[List[float]]):
    """
    chunks: list of {text, document_id, page_number, chunk_index, filename}
    embeddings: parallel list of float vectors
    """
    collection = get_or_create_collection(subject_id)
    if collection is None:
        logger.warning("Vector store unavailable; chunks not indexed.")
        return

    ids, docs, metas, embeds = [], [], [], []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        if not emb:
            continue
        chunk_id = f"{chunk.get('document_id', 'doc')}_{chunk.get('page_number', 0)}_{chunk.get('chunk_index', i)}"
        ids.append(chunk_id)
        docs.append(chunk["text"])
        metas.append({
            "document_id": chunk.get("document_id", ""),
            "subject_id": subject_id,
            "page_number": chunk.get("page_number", 0),
            "chunk_index": chunk.get("chunk_index", i),
            "filename": chunk.get("filename", ""),
        })
        embeds.append(emb)

    if not ids:
        return

    try:
        collection.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeds)
        logger.info(f"Indexed {len(ids)} chunks into collection '{_collection_name(subject_id)}'")
    except Exception as exc:
        logger.error(f"Vector upsert error: {exc}")


def similarity_search(subject_id: str, query_embedding: List[float],
                      top_k: int = 5) -> List[Dict]:
    """
    Return top-k similar chunks with metadata.
    """
    collection = get_or_create_collection(subject_id)
    if collection is None:
        return []
    if not query_embedding:
        return []
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count() or top_k),
            include=["documents", "metadatas", "distances"],
        )
        chunks = []
        for doc, meta, dist in zip(
            results.get("documents", [[]])[0],
            results.get("metadatas", [[]])[0],
            results.get("distances", [[]])[0],
        ):
            chunks.append({
                "text": doc,
                "metadata": meta,
                "score": 1 - dist,  # cosine similarity
            })
        return chunks
    except Exception as exc:
        logger.error(f"Similarity search error: {exc}")
        return []


def delete_collection(subject_id: str):
    client = _get_client()
    if client is None:
        return
    try:
        client.delete_collection(_collection_name(subject_id))
    except Exception as exc:
        logger.warning(f"Could not delete collection: {exc}")

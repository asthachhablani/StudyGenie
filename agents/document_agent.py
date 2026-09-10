"""
Document Processing Agent — orchestrates PDF extraction, chunking,
embedding generation, and vector-store indexing.
"""
import logging
from models.document_model import (update_document_status, save_chunks,
                                    delete_chunks_for_document)
from services.pdf_service import extract_and_chunk
from services.embedding_service import embed_texts
from services.vector_service import add_chunks_to_vector_store
from config import Config

logger = logging.getLogger(__name__)


class DocumentAgent:
    """Processes an uploaded PDF document end-to-end."""

    def process(self, doc_id: str, file_path: str, subject_id: str, user_id: str):
        logger.info(f"[DocumentAgent] Starting processing for doc_id={doc_id}")
        update_document_status(doc_id, "processing")

        # 1. Extract and chunk
        try:
            result = extract_and_chunk(
                file_path,
                chunk_size=Config.CHUNK_SIZE,
                overlap=Config.CHUNK_OVERLAP,
            )
        except Exception as exc:
            logger.error(f"[DocumentAgent] Extraction failed: {exc}")
            update_document_status(doc_id, "failed", {"error": str(exc)})
            return

        if not result["chunks"]:
            update_document_status(doc_id, "failed",
                                   {"error": "No extractable text found in PDF."})
            return

        # 2. Generate embeddings
        texts = [c["text"] for c in result["chunks"]]
        try:
            embeddings = embed_texts(texts)
        except Exception as exc:
            logger.error(f"[DocumentAgent] Embedding generation failed: {exc}")
            embeddings = [[] for _ in texts]

        # 3. Prepare chunk documents for MongoDB
        from pathlib import Path
        filename = Path(file_path).name
        mongo_chunks = []
        for idx, (chunk, emb) in enumerate(zip(result["chunks"], embeddings)):
            mongo_chunks.append({
                "document_id": doc_id,
                "subject_id": subject_id,
                "user_id": user_id,
                "text": chunk["text"],
                "page_number": chunk.get("page_number", 0),
                "chunk_index": chunk.get("chunk_index", idx),
                "filename": filename,
            })

        # 4. Store chunks in MongoDB
        delete_chunks_for_document(doc_id)
        save_chunks(mongo_chunks)

        # 5. Index in vector store
        vector_chunks = [
            {
                "text": c["text"],
                "document_id": doc_id,
                "page_number": c.get("page_number", 0),
                "chunk_index": c.get("chunk_index", idx),
                "filename": filename,
            }
            for idx, c in enumerate(result["chunks"])
        ]
        add_chunks_to_vector_store(subject_id, vector_chunks, embeddings)

        # 6. Mark document as processed
        update_document_status(doc_id, "processed", {
            "page_count": result["page_count"],
            "chunk_count": len(result["chunks"]),
        })
        logger.info(f"[DocumentAgent] Finished: {len(result['chunks'])} chunks indexed for doc_id={doc_id}")

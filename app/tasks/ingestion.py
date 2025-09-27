# app/tasks/ingestion.py
import uuid
from app.services.extraction import extract_full_text
from app.services.chunking import chunk_text
from app.services.embeddings import get_embeddings
from app.services.vector_db import upsert_chunks
from app.db.session import SessionLocal
from app.models.document import Document
from app.config.settings import settings

def start_ingestion_for_document(document_id: str, file_path: str, user_id: str):
    """
    Background task: extract text, chunk, embed, and upsert to Pinecone.
    """
    db = SessionLocal()
    try:
        # 1) extract full text
        full_text = extract_full_text(file_path)

        # 2) chunk
        chunks = list(chunk_text(full_text, chunk_size=settings.chunk_size, overlap=settings.chunk_overlap))
        if not chunks:
            # mark doc failed
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "failed"
                db.add(doc)
                db.commit()
            return

        # 3) embeddings (batch)
        embeddings = get_embeddings(chunks)

        # 4) prepare vectors and upsert
        vectors = []
        for i, emb in enumerate(embeddings):
            chunk_id = f"{document_id}_c{i}"
            metadata = {"document_id": document_id, "chunk_id": chunk_id, "text_excerpt": chunks[i][:400]}
            vectors.append({"id": chunk_id, "values": emb, "metadata": metadata})
        upsert_chunks(vectors)

        # 5) update document status
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "indexed"
            db.add(doc)
            db.commit()
    except Exception as e:
        # mark document failed
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "failed"
            db.add(doc)
            db.commit()
        raise
    finally:
        db.close()

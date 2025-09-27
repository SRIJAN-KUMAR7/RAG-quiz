from sqlalchemy.orm import Session
from app.models.document import Document

def get_progress_for_document(db: Session, document_id: str) -> dict:
    """
    Return current status/progress for a document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return {"document_id": document_id, "status": "not_found"}
    return {
        "document_id": document_id,
        "status": doc.status,
        "processing_started_at": doc.processing_started_at,
        "updated_at": doc.updated_at,
    }

def update_progress_for_document(db: Session, document_id: str, status: str) -> bool:
    """
    Update status of a document (e.g. from 'processing' to 'completed').
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return False
    doc.status = status
    db.add(doc)
    db.commit()
    return True

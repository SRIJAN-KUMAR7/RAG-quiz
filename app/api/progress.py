from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.progress_service import get_user_progress_for_document

router = APIRouter()

@router.get("/{user_id}/{document_id}")
def progress(user_id: str, document_id: str, db: Session = Depends(get_db)):
    """
    Return user progress summary for a document.
    """
    prog = get_user_progress_for_document(db, user_id, document_id)
    return {"user_id": user_id, "document_id": document_id, "progress": prog}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services.question_service import list_questions_for_document, trigger_generate_questions

router = APIRouter()

class GenerateRequest(BaseModel):
    document_id: str
    n_mcq: int = 10
    n_match: int = 5
    n_short: int = 5
    regenerate: bool = False

@router.get("/{document_id}")
def list_questions(document_id: str, db: Session = Depends(get_db)):
    """
    Return list of questions (existing + generated) for a document.
    """
    questions = list_questions_for_document(db, document_id)
    return {"document_id": document_id, "questions": questions}

@router.post("/generate")
def generate_questions_endpoint(payload: GenerateRequest, db: Session = Depends(get_db)):
    """
    Trigger generation of new questions for a document.
    """
    try:
        success = trigger_generate_questions(
            db=db,
            document_id=payload.document_id,
            n_mcq=payload.n_mcq,
            n_match=payload.n_match,
            n_short=payload.n_short,
            regenerate=payload.regenerate,
        )
        if not success:
            raise HTTPException(status_code=500, detail="Question generation failed")
        return {"status": "started", "document_id": payload.document_id}
    
    except Exception as e:
        print(f"DEBUG: Exception in generate_questions: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

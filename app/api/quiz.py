from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services.quiz_service import get_next_question_for_user, grade_answer_and_update_progress

router = APIRouter()

class AnswerPayload(BaseModel):
    user_id: str
    document_id: str
    question_id: str
    answer: dict  # For MCQ: {"selected_index": 1} ; For match: mapping ; For short: {"text": "..."}
    elapsed_seconds: Optional[int] = None

@router.get("/next")
def next_question(user_id: str, document_id: str, db: Session = Depends(get_db)):
    q = get_next_question_for_user(db, user_id, document_id)
    if not q:
        return {"message": "No more questions"}
    return q

@router.post("/answer")
def submit_answer(payload: AnswerPayload, db: Session = Depends(get_db)):
    result = grade_answer_and_update_progress(db, payload.user_id, payload.document_id, payload.question_id, payload.answer, payload.elapsed_seconds)
    return result

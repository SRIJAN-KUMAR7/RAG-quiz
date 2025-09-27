# app/services/quiz_service.py
from sqlalchemy.orm import Session
from app.models.progress import UserProgress
from app.models.question import Question
from app.models.document import Document
from typing import Optional

def get_next_question_for_user(db: Session, user_id: str, document_id: str) -> Optional[dict]:
    """
    Returns the next unanswered question for a given user & document.
    """
    # 1. Get user progress for this document
    progress = db.query(UserProgress).filter_by(user_id=user_id, document_id=document_id).first()
    answered_question_ids = progress.answered_question_ids if progress else []

    # 2. Find the next question that hasn't been answered
    next_q = db.query(Question).filter(
        Question.document_id == document_id,
        ~Question.id.in_(answered_question_ids)
    ).order_by(Question.created_at).first()

    if not next_q:
        return None  # quiz completed

    return next_q.to_dict()


def grade_answer_and_update_progress(db: Session, user_id: str, document_id: str, question_id: str, user_answer: str) -> dict:
    """
    Grade the user's answer and update progress.
    """
    question = db.query(Question).filter_by(id=question_id, document_id=document_id).first()
    if not question:
        return {"success": False, "message": "Question not found."}

    # 1. Simple grading logic
    correct = False
    if question.question_type == "mcq":
        correct = question.answer.strip().lower() == user_answer.strip().lower()
    else:
        # For short/match questions, you can use more advanced similarity check
        correct = question.answer.strip().lower() == user_answer.strip().lower()

    # 2. Update user's progress
    progress = db.query(UserProgress).filter_by(user_id=user_id, document_id=document_id).first()
    if not progress:
        progress = UserProgress(user_id=user_id, document_id=document_id, answered_question_ids=[])
        db.add(progress)

    progress.answered_question_ids.append(question_id)
    if correct:
        progress.score = (progress.score or 0) + 1
    db.commit()

    return {"success": True, "correct": correct, "current_score": progress.score}

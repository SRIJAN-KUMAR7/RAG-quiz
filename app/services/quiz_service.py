from sqlalchemy.orm import Session
from app.models.progress import UserProgress
from app.models.question import Question
from app.models.document import Document
from typing import Optional, Dict
import uuid
import json


def get_next_question_for_user(db: Session, user_id: str, document_id: str) -> Optional[dict]:
    """
    Returns the next unanswered question for a given user & document.
    """
    progress = db.query(UserProgress).filter_by(user_id=user_id, document_id=document_id).first()
    answered_question_ids = progress.answered_question_ids if progress else []

    # Ensure all answered_question_ids are strings for comparison
    answered_question_ids = [str(q) for q in answered_question_ids]

    next_q = (
        db.query(Question)
        .filter(Question.document_id == document_id)
        .filter(~Question.id.in_(answered_question_ids))
        .order_by(Question.created_at)
        .first()
    )

    if not next_q:
        return None  # all questions answered

    return next_q.to_dict()


def grade_answer_and_update_progress(
    db: Session,
    user_id: str,
    document_id: str,
    question_id: str,
    user_answer: Dict,
    elapsed_seconds: Optional[int] = None
) -> dict:
    """
    Grade the user's answer and update progress.
    """
    question = db.query(Question).filter_by(id=question_id, document_id=document_id).first()
    if not question:
        return {"success": False, "message": "Question not found."}

    correct = False

    if question.question_type == "mcq":
        # user_answer expected to be {"selected_index": int}
        selected_index = user_answer.get("selected_index")
        if selected_index is not None and question.options and 0 <= selected_index < len(question.options):
            selected_option = question.options[selected_index].strip().lower()
            correct = selected_option == question.answer.strip().lower()

    elif question.question_type == "short":
        # user_answer expected to be {"text": "..."}
        user_text = user_answer.get("text", "").strip().lower()
        correct = user_text == question.answer.strip().lower()

    else:
        # For other types (match etc.), fallback to string compare
        try:
            user_text = json.dumps(user_answer).strip().lower()
        except Exception:
            user_text = str(user_answer).strip().lower()
        correct = user_text == question.answer.strip().lower()

    # Update user progress
    progress = db.query(UserProgress).filter_by(user_id=user_id, document_id=document_id).first()
    if not progress:
        progress = UserProgress(user_id=user_id, document_id=document_id, answered_question_ids=[])
        db.add(progress)

    question_id_str = str(question_id)
    if not progress.answered_question_ids:
        progress.answered_question_ids = []

    if question_id_str not in progress.answered_question_ids:
        progress.answered_question_ids.append(question_id_str)

    if correct:
        progress.score = (progress.score or 0) + 1

    db.commit()

    return {"success": True, "correct": correct, "current_score": progress.score}

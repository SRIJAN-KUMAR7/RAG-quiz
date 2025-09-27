# app/services/question_service.py
from sqlalchemy.orm import Session
from typing import List, Dict

from app.models.question import Question
from app.models.document import Document
from app.services import vector_db, llm_client  

def list_questions_for_document(db: Session, document_id: str) -> List[Dict]:
    """
    Get all questions already generated/stored for a document.
    """
    questions = db.query(Question).filter_by(document_id=document_id).all()
    return [q.to_dict() for q in questions]


def trigger_generate_questions(
    db: Session,
    document_id: str,
    n_mcq: int = 10,
    n_match: int = 5,
    n_short: int = 5,
    regenerate: bool = False,
) -> bool:
    """
    Orchestrate the generation of new questions for a document.
    Steps:
      1. Retrieve the document & related chunks from Pinecone.
      2. Ask Gemini to generate MCQs/match/short-answer questions.
      3. Save the generated questions to Postgres.
    """

    doc = db.query(Document).filter_by(id=document_id).first()
    if not doc:
        return False

    if regenerate:
        db.query(Question).filter_by(document_id=document_id).delete()
        db.commit()

  
    chunks = vector_db.fetch_chunks_for_document(document_id)
    if not chunks:
        return False

    generated_questions = llm_client.generate_questions(
        chunks_text=[c["text"] for c in chunks],
        n_mcq=n_mcq,
        n_match=n_match,
        n_short=n_short,
    )

    for q in generated_questions:
        question = Question(
            document_id=document_id,
            question_type=q["type"],  
            question_text=q["question"],
            options=q.get("options"),
            answer=q.get("answer")
        )
        db.add(question)

    db.commit()
    return True

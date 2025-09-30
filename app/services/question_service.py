from sqlalchemy.orm import Session
from typing import List, Dict
import uuid

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
    """
    try:
        print(f"DEBUG: Starting question generation for document: {document_id}")
        
        doc = db.query(Document).filter_by(id=document_id).first()
        if not doc:
            print(f"DEBUG: Document {document_id} not found")
            return False

        print(f"DEBUG: Document found: {doc.filename}")

        if regenerate:
            print("DEBUG: Regenerating - deleting existing questions")
            db.query(Question).filter_by(document_id=document_id).delete()
            db.commit()

        # Step 1: Fetch chunks from Pinecone
        print("DEBUG: Fetching chunks from Pinecone")
        chunks = vector_db.fetch_chunks_for_document(document_id, top_k=10)
        
        if not chunks:
            print("DEBUG: No chunks found, creating fallback content")
            chunks = [{'text': f'Content from document: {doc.filename}'}]

        print(f"DEBUG: Found {len(chunks)} chunks")

        # Step 2: Generate questions using LLM
        print("DEBUG: Generating questions with LLM")
        chunks_text = [chunk['text'] for chunk in chunks]
        
        generated_questions = llm_client.generate_questions(
            chunks_text=chunks_text,
            n_mcq=n_mcq,
            n_short=n_short,
        )

        print(f"DEBUG: Generated {len(generated_questions)} questions")

        # Step 3: Save questions to database ONE BY ONE to avoid UUID issues
        print("DEBUG: Saving questions to database")
        saved_count = 0
        for i, q in enumerate(generated_questions):
            try:
                question = Question(
                    document_id=str(document_id),
                    question_type=q["type"],
                    question_text=q["question"],
                    options=q.get("options"),
                    answer=q.get("answer")
                )
                db.add(question)
                db.flush()  # Flush individually to catch errors early
                saved_count += 1
                print(f"DEBUG: Saved question {i+1}/{len(generated_questions)}")
            except Exception as e:
                print(f"DEBUG: Error saving question {i+1}: {e}")
                db.rollback()
                continue

        if saved_count > 0:
            db.commit()
            print(f"DEBUG: Successfully saved {saved_count} questions")
            return True
        else:
            print("DEBUG: No questions were saved")
            return False

    except Exception as e:
        print(f"DEBUG: Error in trigger_generate_questions: {e}")
        import traceback
        traceback.print_exc()
        try:
            db.rollback()
        except:
            pass
        return False

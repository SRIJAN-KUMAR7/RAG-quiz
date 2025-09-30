import fitz  # PyMuPDF
import google.generativeai as genai
import logging
import json
import re
from fastapi import UploadFile, APIRouter, Depends
from sqlalchemy.orm import Session
from google.api_core.exceptions import ResourceExhausted
from app.config.settings import settings
from app.db.session import get_db
from app.models.question import Question

logging.basicConfig(level=logging.DEBUG)
genai.configure(api_key=settings.gemini_api_key)
MODEL_NAME = "gemini-2.5-pro"

router = APIRouter()


# --- PDF Text Extraction ---
async def extract_text_from_pdf(file: UploadFile) -> str:
    """
    Extract text from a PDF file (UploadFile.file object)
    """
    file_bytes = await file.read()
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


# --- Gemini Question Generation ---
def generate_questions_from_text(text: str) -> list[dict]:
    """
    Generate MCQs + short answer questions using Gemini API.
    Returns a Python list of question dictionaries.
    """
    prompt = f"""
You are an intelligent question generator. You must generate questions strictly based on the provided document content. 
Do NOT invent information. Only extract concepts, facts, or statements from the content to create the questions.

Instructions:
1. Generate exactly 5 multiple choice questions (MCQs) and 3 short answer questions.
2. For MCQs:
   - Provide 4 options labeled A), B), C), D)
   - Clearly indicate the correct option in the "answer" field
   - Questions must be clear, concise, and answerable using the document content only
3. For short answer questions:
   - Provide a concise answer that is fully contained in the document content
4. Return ONLY a JSON array with no extra text or explanation

Document Content:
{text}

Return a JSON array of exactly 8 questions.
"""

    model = genai.GenerativeModel(MODEL_NAME)
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        logging.debug(f"Raw Gemini response: {raw_text[:500]}")  # log first 500 chars

        # Attempt to parse JSON safely
        match = re.search(r'(\[.*\])', raw_text, re.DOTALL)
        if match:
            questions = json.loads(match.group(1))
            if isinstance(questions, list):
                return questions

        logging.error("Failed to parse questions JSON from Gemini response.")
        return []

    except ResourceExhausted:
        logging.error("Gemini API quota exceeded.")
        return []
    except Exception as e:
        logging.error(f"Unexpected error from Gemini API: {e}")
        return []


# --- Save Questions to Database ---
def save_questions_to_db(questions: list[dict], db: Session, document_id: str):
    for q in questions:
        question_obj = Question(
            document_id=document_id,
            question_type=q.get("type"),          
            question_text=q.get("question"),       
            options=q.get("options") if q.get("options") else None,
            answer=q.get("answer")
        )
        db.add(question_obj)
    db.commit()



# --- FastAPI Endpoint ---
@router.post("/skillquestion-generate")
async def upload_pdf(file: UploadFile, db: Session = Depends(get_db)):
    try:
        text = await extract_text_from_pdf(file)
        if not text.strip():
            return {"detail": "Uploaded PDF is empty or contains no extractable text."}

        questions = generate_questions_from_text(text)
        if not questions:
            return {"detail": "Failed to generate questions from the document."}

        document_id = "some-document-id"  # Replace with Goal ID logic
        
        save_questions_to_db(questions, db, document_id)

        return {"detail": f"{len(questions)} questions saved successfully."}

    except Exception as e:
        logging.error(f"Error in upload_pdf endpoint: {e}")
        return {"detail": "Internal server error"}

import uuid
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db

# tasks module should implement ingestion task (Celery or sync)
from app.tasks.ingestion import start_ingestion_for_document

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()

@router.post("/")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Upload PDF. Saves file, creates document metadata row (in tasks.ingestion),
    and enqueues ingestion.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    document_id = str(uuid.uuid4())
    dest_path = UPLOAD_DIR / f"{document_id}.pdf"
    # save file
    with open(dest_path, "wb") as f:
        f.write(await file.read())

    # Enqueue ingestion as background task (this function should create DB row, etc.)
    # start_ingestion_for_document should accept (document_id, file_path, user_id, db) and
    # either schedule a Celery job or run ingestion synchronously (depending on implementation).
    background_tasks.add_task(start_ingestion_for_document, document_id, str(dest_path), user_id)

    return JSONResponse({"document_id": document_id, "filename": file.filename})

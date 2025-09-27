import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.document import Document
from app.tasks.ingestion import start_ingestion_for_document
from app.config.settings import settings

UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()

# Use a hardcoded dummy user
DUMMY_USER_ID = "dummy-user-1"

@router.post("/")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    document_id = str(uuid.uuid4())
    dest_path = UPLOAD_DIR / f"{document_id}.pdf"
    with open(dest_path, "wb") as f:
        f.write(content)

    doc = Document(
        id=document_id,
        user_id=DUMMY_USER_ID,
        filename=file.filename,
        file_path=str(dest_path),
        status="processing",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(doc)
    db.commit()

    background_tasks.add_task(start_ingestion_for_document, document_id, str(dest_path), DUMMY_USER_ID)

    return JSONResponse({"document_id": document_id, "status": "processing"})

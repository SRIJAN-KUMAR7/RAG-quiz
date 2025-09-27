from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.api import upload  
from app.services.vector_db import init_pinecone
from app.db.session import Base, engine
import app.models.user, app.models.document, app.models.question, app.models.progress  # ensures models imported

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_pinecone()
    except Exception as e:
        print("⚠️ Pinecone init failed:", e)
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="RAG Quiz Microservice", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(upload.router, prefix="/upload", tags=["upload"])

@app.get("/")
def read_root():
    return {"message": "Welcome to RAG QUIZ Microservice"}

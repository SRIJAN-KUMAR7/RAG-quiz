from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.api import upload  
from app.services.vector_db import init_pinecone
from app.db.session import Base, engine
from app.api import questions
from app.models import document, progress, question, user

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_pinecone()
    except Exception as e:
        print("Pinecone init failed:", e)
    
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"DEBUG: Existing database tables: {tables}")
    
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"DEBUG: Tables after creation: {tables}")
    
    yield

app = FastAPI(title="RAG Quiz Microservice", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(questions.router, prefix="/questions", tags=["questions"]) 

@app.get("/")
def read_root():
    return {"message": "Welcome to RAG QUIZ Microservice"}

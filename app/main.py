from fastapi import FastAPI
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app:FastAPI):
    print("Starting Up.....")
    #DB calls
    #close calls
    yield
    print("Shutting Down....RAG.....")


app=FastAPI(title="RAG for Quiz Microservice",lifespan=lifespan)

@app.get('/')
def read_root():
    return {"message":"Welcome to RAG QUIZ Microservice"}


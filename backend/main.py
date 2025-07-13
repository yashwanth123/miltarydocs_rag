from fastapi import FastAPI
from pydantic import BaseModel
from backend.services.embedding_service import ask_question  # adjust import path if needed

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def root():
    return {"message": "Backend running"}

@app.post("/ask")
def ask(request: QueryRequest):
    return {"answer": ask_question(request.query)}

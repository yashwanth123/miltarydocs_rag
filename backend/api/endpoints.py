from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.embedding_service import ask_question

router = APIRouter()

class QueryRequest(BaseModel):
    question: str

@router.get("/")
def root():
    return {"message": "Backend running"}

@router.post("/ask")
def ask(request: QueryRequest):
    answer = ask_question(request.question)
    return {"answer": answer}

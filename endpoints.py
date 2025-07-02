from fastapi import APIRouter
from backend.services.embedding_service import ask_question

router = APIRouter()


@router.get("/")
def root():
    return {"status": "API is running"}


@router.get("/ask/")
def ask(q: str):
    results = ask_question(q)
    return {"results": results}

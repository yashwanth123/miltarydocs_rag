from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.services.embedding_service import ask_question

router = APIRouter()

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    mask_sensitive: bool = True


@router.post("/ask")
def ask(request: QueryRequest):
    return ask_question(request.query, mask_sensitive=request.mask_sensitive)

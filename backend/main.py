from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.services.embedding_service import ask_question
from backend.vector_store.chroma_client import collection_count

load_dotenv()

app = FastAPI(title="MilitaryDocs RAG", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    mask_sensitive: bool = True


@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "indexed_chunks": collection_count(),
    }


@app.post("/ask")
def ask(request: QueryRequest):
    return ask_question(request.query, mask_sensitive=request.mask_sensitive)

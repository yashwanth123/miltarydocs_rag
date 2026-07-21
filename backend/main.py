from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.services.embedding_service import ask_question
from backend.services.retrieval_service import refresh_lexical_index
from backend.services.upload_service import ingest_saved_file, list_data_files, save_upload
from backend.vector_store.chroma_client import (
    collection_count,
    embeddings_ready,
    get_embeddings,
)

load_dotenv()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Loading embedding model (first start may take a moment)...")
    get_embeddings()
    print("Building lexical search index...")
    indexed = refresh_lexical_index()
    print(f"Ready. Indexed chunks: {collection_count()} (lexical index: {indexed})")
    yield


app = FastAPI(title="Military Recruit Guide RAG", version="3.0.0", lifespan=lifespan)

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
    branch: str | None = Field(default="all", max_length=32)


@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health():
    ready = embeddings_ready()
    return {
        "status": "ok" if ready else "starting",
        "ready": ready,
        "indexed_chunks": collection_count() if ready else 0,
        "files": list_data_files() if ready else [],
        "branches": ["all", "general", "army", "navy", "air_force", "marines", "coast_guard", "space_force"],
    }


@app.post("/ask")
def ask(request: QueryRequest):
    return ask_question(
        request.query,
        mask_sensitive=request.mask_sensitive,
        branch=request.branch,
    )


@app.post("/upload")
async def upload(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    results = []
    total_chunks = 0

    for upload_file in files:
        content = await upload_file.read()
        try:
            saved_path = save_upload(upload_file.filename, content)
            result = ingest_saved_file(saved_path)
            total_chunks += result["chunks_added"]
            results.append(result)
        except ValueError as exc:
            results.append({"filename": upload_file.filename, "error": str(exc)})

    refresh_lexical_index()

    return {
        "results": results,
        "indexed_chunks": collection_count(),
        "files": list_data_files(),
        "message": f"Upload complete. Added {total_chunks} chunks.",
    }

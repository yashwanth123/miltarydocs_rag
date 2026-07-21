from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.services.embedding_service import ask_question
from backend.services.upload_service import ingest_saved_file, list_data_files, save_upload
from backend.vector_store.chroma_client import collection_count

load_dotenv()

app = FastAPI(title="MilitaryDocs RAG", version="2.1.0")

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
        "files": list_data_files(),
    }


@app.post("/ask")
def ask(request: QueryRequest):
    return ask_question(request.query, mask_sensitive=request.mask_sensitive)


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

    return {
        "results": results,
        "indexed_chunks": collection_count(),
        "files": list_data_files(),
        "message": f"Upload complete. Added {total_chunks} chunks.",
    }

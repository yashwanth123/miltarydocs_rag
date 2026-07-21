from pathlib import Path

from scripts.ingest_documents import DATA_DIR, SUPPORTED_EXTENSIONS, ingest_file
from backend.vector_store.chroma_client import add_to_index, collection_count

MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def list_data_files() -> list[str]:
    if not DATA_DIR.exists():
        return []
    return sorted(
        path.name
        for path in DATA_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def save_upload(filename: str, content: bytes) -> Path:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")

    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("File is too large. Maximum size is 20 MB.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name
    target = DATA_DIR / safe_name
    target.write_bytes(content)
    return target


def ingest_saved_file(path: Path) -> dict:
    documents = ingest_file(path)
    if not documents:
        return {
            "filename": path.name,
            "chunks_added": 0,
            "message": f"No readable text found in {path.name}.",
        }

    added = add_to_index(documents)
    return {
        "filename": path.name,
        "chunks_added": added,
        "message": f"Indexed {added} new chunks from {path.name}.",
    }

from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document

from backend.utils.chunker import chunk_text
from backend.utils.doc_metadata import build_chunk_metadata, parse_frontmatter
from backend.utils.docx_parser import extract_text_from_docx
from backend.utils.masking import is_low_quality_chunk
from backend.utils.pdf_parser import extract_text_from_pdf
from backend.vector_store.chroma_client import (
    add_to_index,
    collection_count,
    remove_documents_by_source,
    reset_collection,
)
from scripts.reference_detector import detect_references

load_dotenv()

DATA_DIR = Path("data")
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def load_text_file(file_path: Path) -> list[tuple[int, str]]:
    raw = file_path.read_text(encoding="utf-8", errors="ignore")
    _metadata, body = parse_frontmatter(raw)
    return [(1, body)] if body.strip() else []


def discover_files(root: Path | None = None) -> list[Path]:
    base = root or DATA_DIR
    if not base.exists():
        return []

    files: list[Path] = []
    for path in sorted(base.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return files


def ingest_file(file_path: Path) -> list[Document]:
    pages: list[tuple[int, str]] = []
    suffix = file_path.suffix.lower()
    frontmatter: dict = {}

    if suffix == ".pdf":
        pages = extract_text_from_pdf(str(file_path))
        frontmatter = {}
    elif suffix == ".txt":
        raw = file_path.read_text(encoding="utf-8", errors="ignore")
        frontmatter, body = parse_frontmatter(raw)
        pages = [(1, body)] if body.strip() else []
    elif suffix == ".docx":
        pages = extract_text_from_docx(str(file_path))
        frontmatter = {}

    documents: list[Document] = []
    for page_num, page_text in pages:
        chunks = chunk_text(page_text)
        refs = detect_references(page_text)
        for chunk in chunks:
            if is_low_quality_chunk(chunk):
                continue
            documents.append(
                Document(
                    page_content=chunk,
                    metadata=build_chunk_metadata(file_path, page_num, refs, frontmatter),
                )
            )
    return documents


def ingest_all(root: Path | None = None, reset: bool = False) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if reset:
        print("Resetting local vector store...")
        reset_collection()

    files = discover_files(root)
    if not files:
        print(f"No supported files found under {root or DATA_DIR}.")
        return {"files": 0, "chunks": 0, "total": collection_count()}

    all_docs: list[Document] = []
    for file_path in files:
        print(f"Processing {file_path}...")
        relative_source = str(file_path.relative_to(Path("data")))
        remove_documents_by_source(relative_source)
        docs = ingest_file(file_path)
        all_docs.extend(docs)
        print(f"  -> {len(docs)} chunks")

    added = add_to_index(all_docs)

    try:
        from backend.services.retrieval_service import refresh_lexical_index

        indexed = refresh_lexical_index()
        print(f"Lexical index refreshed ({indexed} chunks).")
    except Exception as exc:
        print(f"Warning: could not refresh lexical index: {exc}")

    total = collection_count()
    print(f"Ingestion complete: {added} chunks indexed ({total} total in store).")
    return {"files": len(files), "chunks": added, "total": total}


def main(reset: bool = False) -> None:
    ingest_all(root=DATA_DIR, reset=reset)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest military documents into ChromaDB")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear the local vector store before ingesting",
    )
    parser.add_argument(
        "--public-only",
        action="store_true",
        help="Ingest only files under data/public/",
    )
    args = parser.parse_args()
    root = DATA_DIR / "public" if args.public_only else DATA_DIR
    ingest_all(root=root, reset=args.reset)

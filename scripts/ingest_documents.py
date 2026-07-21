from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document

from backend.utils.chunker import chunk_text
from backend.utils.docx_parser import extract_text_from_docx
from backend.utils.masking import is_low_quality_chunk
from backend.utils.pdf_parser import extract_text_from_pdf
from backend.vector_store.chroma_client import add_to_index, collection_count, reset_collection
from scripts.reference_detector import detect_references

load_dotenv()

DATA_DIR = Path("data")
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def load_text_file(file_path: Path) -> list[tuple[int, str]]:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    return [(1, text)] if text.strip() else []


def ingest_file(file_path: Path) -> list[Document]:
    pages: list[tuple[int, str]] = []
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        pages = extract_text_from_pdf(str(file_path))
    elif suffix == ".txt":
        pages = load_text_file(file_path)
    elif suffix == ".docx":
        pages = extract_text_from_docx(str(file_path))

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
                    metadata={
                        "source": file_path.name,
                        "page": page_num,
                        "references": ", ".join(refs) if refs else "",
                    },
                )
            )
    return documents


def main(reset: bool = False) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if reset:
        print("Resetting local vector store...")
        reset_collection()

    all_docs: list[Document] = []
    files = sorted(
        path
        for path in DATA_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not files:
        print(f"No supported files found in {DATA_DIR}. Add PDF, TXT, or DOCX files first.")
        return

    for file_path in files:
        print(f"Processing {file_path.name}...")
        docs = ingest_file(file_path)
        all_docs.extend(docs)
        print(f"  -> {len(docs)} chunks")

    added = add_to_index(all_docs)
    print(f"Ingestion complete: {added} chunks indexed ({collection_count()} total in store).")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest military documents into ChromaDB")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear the local vector store before ingesting",
    )
    args = parser.parse_args()
    main(reset=args.reset)

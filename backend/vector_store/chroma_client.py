import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Reduce background writes/noise from Chroma telemetry
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY", "False")

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "military-docs")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

_embeddings: HuggingFaceEmbeddings | None = None
_vector_store: Chroma | None = None
_embeddings_ready = False


def embeddings_ready() -> bool:
    return _embeddings_ready


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings, _embeddings_ready
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        _embeddings_ready = True
    return _embeddings


def get_vector_store() -> Chroma:
    global _vector_store
    if _vector_store is None:
        Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
        _vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=get_embeddings(),
            persist_directory=CHROMA_DIR,
        )
    return _vector_store


def add_to_index(documents: list) -> int:
    if not documents:
        return 0
    store = get_vector_store()
    store.add_documents(documents)
    return len(documents)


def get_retriever(search_k: int = 4):
    return get_vector_store().as_retriever(search_kwargs={"k": search_k})


def collection_count() -> int:
    try:
        return get_vector_store()._collection.count()
    except Exception:
        return 0


def reset_collection() -> None:
    global _vector_store
    _vector_store = None

    chroma_path = Path(CHROMA_DIR)
    if chroma_path.exists():
        shutil.rmtree(chroma_path)
    chroma_path.mkdir(parents=True, exist_ok=True)

    get_vector_store()

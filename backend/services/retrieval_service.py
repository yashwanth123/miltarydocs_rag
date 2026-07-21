import os
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_core.documents import Document

from backend.vector_store.chroma_client import get_all_documents, get_retriever

load_dotenv()

USE_HYBRID_SEARCH = os.getenv("USE_HYBRID_SEARCH", "true").lower() == "true"
USE_RERANKER = os.getenv("USE_RERANKER", "true").lower() == "true"
BM25_K = int(os.getenv("BM25_K", "8"))
VECTOR_K = int(os.getenv("VECTOR_K", "8"))
RERANK_TOP_N = int(os.getenv("RERANK_TOP_N", "8"))
FINAL_K = int(os.getenv("FINAL_K", "4"))
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

_bm25_index = None
_bm25_docs: list[Document] = []
_reranker = None


@dataclass
class ScoredDocument:
    document: Document
    score: float


def _tokenize(text: str) -> list[str]:
    return [token for token in text.lower().split() if len(token) > 1]


def refresh_lexical_index() -> int:
    global _bm25_index, _bm25_docs

    from rank_bm25 import BM25Okapi

    documents = get_all_documents()
    _bm25_docs = documents
    if not documents:
        _bm25_index = None
        return 0

    corpus = [_tokenize(doc.page_content) for doc in documents]
    _bm25_index = BM25Okapi(corpus)
    return len(documents)


def _get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder

        _reranker = CrossEncoder(RERANKER_MODEL)
    return _reranker


def _matches_branch(doc: Document, branch: str | None) -> bool:
    if not branch or branch in {"all", "general"}:
        return True

    doc_branch = (doc.metadata or {}).get("branch", "general")
    return doc_branch in {branch, "general"}


def _bm25_search(query: str, branch: str | None, limit: int) -> list[ScoredDocument]:
    if _bm25_index is None or not _bm25_docs:
        return []

    scores = _bm25_index.get_scores(_tokenize(query))
    ranked = sorted(
        (
            ScoredDocument(document=doc, score=float(score))
            for doc, score in zip(_bm25_docs, scores)
            if _matches_branch(doc, branch)
        ),
        key=lambda item: item.score,
        reverse=True,
    )
    return [item for item in ranked if item.score > 0][:limit]


def _vector_search(query: str, branch: str | None, limit: int) -> list[ScoredDocument]:
    retriever = get_retriever(search_k=max(limit * 2, limit))
    docs = retriever.invoke(query)

    filtered = [doc for doc in docs if _matches_branch(doc, branch)]
    return [
        ScoredDocument(document=doc, score=float(limit - index))
        for index, doc in enumerate(filtered[:limit])
    ]


def _reciprocal_rank_fusion(
    result_lists: list[list[ScoredDocument]],
    k: int = 60,
) -> list[ScoredDocument]:
    scores: dict[str, float] = {}
    docs_by_key: dict[str, Document] = {}

    for results in result_lists:
        for rank, item in enumerate(results):
            key = item.document.page_content[:160]
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            docs_by_key[key] = item.document

    ranked = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
    return [ScoredDocument(document=docs_by_key[key], score=score) for key, score in ranked]


def _rerank(query: str, candidates: list[ScoredDocument], top_n: int) -> list[Document]:
    if not candidates:
        return []

    if not USE_RERANKER:
        return [item.document for item in candidates[:top_n]]

    reranker = _get_reranker()
    pairs = [(query, item.document.page_content) for item in candidates]
    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(candidates, scores),
        key=lambda pair: float(pair[1]),
        reverse=True,
    )
    return [item.document for item, _score in ranked[:top_n]]


def hybrid_retrieve(
    queries: list[str],
    branch: str | None = None,
    final_k: int | None = None,
) -> list[Document]:
    final_k = final_k or FINAL_K
    fused: list[ScoredDocument] = []

    for query in queries:
        vector_results = _vector_search(query, branch, VECTOR_K)
        if USE_HYBRID_SEARCH:
            bm25_results = _bm25_search(query, branch, BM25_K)
            fused = _reciprocal_rank_fusion([vector_results, bm25_results])
        else:
            fused = vector_results

    if not fused and queries:
        fused = _vector_search(queries[0], branch, VECTOR_K)

    candidates = fused[: max(RERANK_TOP_N, final_k)]
    return _rerank(queries[0], candidates, final_k)

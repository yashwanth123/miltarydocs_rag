import os

from dotenv import load_dotenv
from langchain_community.llms import HuggingFacePipeline
from transformers import pipeline

from backend.services.answer_builder import (
    build_extractive_answer,
    build_identity_answer,
    build_meta_answer,
    build_summary_answer,
    build_vague_answer,
    is_identity_question,
    is_meta_question,
    is_summarize_intent,
    is_vague_question,
    is_weak_model_answer,
)
from backend.utils.masking import filter_documents, mask_documents
from backend.vector_store.chroma_client import collection_count, get_retriever

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "google/flan-t5-large")
SEARCH_K = int(os.getenv("SEARCH_K", "6"))
USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"

_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        generator = pipeline(
            "text2text-generation",
            model=LLM_MODEL,
            max_new_tokens=180,
            do_sample=False,
        )
        _llm = HuggingFacePipeline(pipeline=generator)
    return _llm


def _maybe_enhance_with_llm(question: str, context: str, draft_answer: str) -> str:
    if not USE_LLM:
        return draft_answer

    prompt = (
        "Rewrite the draft answer so it is clear, helpful, and grounded in the context. "
        "Do not invent facts.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n"
        f"Draft answer: {draft_answer}\n"
        "Final answer:"
    )

    try:
        enhanced = _get_llm().invoke(prompt).strip()
        if is_weak_model_answer(enhanced):
            return draft_answer
        return enhanced
    except Exception:
        return draft_answer


def ask_question(question: str, mask_sensitive: bool = True) -> dict:
    cleaned_question = question.strip()

    if collection_count() == 0:
        return {
            "answer": (
                "No documents are indexed yet. Add PDF, DOCX, or TXT files to the data/ folder "
                "and run `python scripts/ingest_documents.py --reset`."
            ),
            "sources": [],
            "masked": mask_sensitive,
            "document_count": 0,
        }

    if is_vague_question(cleaned_question):
        return {
            "answer": build_vague_answer(),
            "sources": [],
            "masked": mask_sensitive,
            "document_count": collection_count(),
        }

    retriever = get_retriever(search_k=SEARCH_K)
    raw_docs = retriever.get_relevant_documents(cleaned_question)
    docs = filter_documents(raw_docs) or raw_docs

    if is_meta_question(cleaned_question):
        answer = build_meta_answer(cleaned_question, docs, collection_count())
    elif is_identity_question(cleaned_question):
        answer = build_identity_answer(docs)
    elif is_summarize_intent(cleaned_question):
        answer = build_summary_answer(docs)
    elif not docs:
        answer = build_vague_answer()
    else:
        answer = build_extractive_answer(cleaned_question, docs)
        context = "\n\n".join(doc.page_content for doc in docs[:3])
        answer = _maybe_enhance_with_llm(cleaned_question, context, answer)

    sources = mask_documents(docs[:3], enabled=mask_sensitive) if docs else []

    return {
        "answer": answer,
        "sources": sources,
        "masked": mask_sensitive,
        "document_count": collection_count(),
    }

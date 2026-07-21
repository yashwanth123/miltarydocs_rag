import os

from dotenv import load_dotenv

from backend.services.answer_builder import (
    build_answer_for_intent,
    build_out_of_scope_answer,
    build_vague_answer,
    is_weak_model_answer,
)
from backend.services.guardrails import apply_answer_guardrails
from backend.services.query_intent import (
    Intent,
    NO_RETRIEVAL_INTENTS,
    classify_intent,
    expand_retrieval_queries,
    is_out_of_scope,
    is_vague_question,
)
from backend.services.retrieval_service import hybrid_retrieve
from backend.utils.masking import filter_documents, mask_documents
from backend.vector_store.chroma_client import collection_count

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "google/flan-t5-large")
USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"

_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        from langchain_community.llms import HuggingFacePipeline
        from transformers import pipeline

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
        "Rewrite the draft answer in a natural, conversational tone. "
        "Keep all facts from the draft. Do not invent information.\n\n"
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


def _retrieve_documents(question: str, intent: Intent, branch: str | None = None) -> list:
    queries = expand_retrieval_queries(question, intent)
    docs = hybrid_retrieve(queries, branch=branch)
    return filter_documents(docs) or docs


def ask_question(
    question: str,
    mask_sensitive: bool = True,
    branch: str | None = None,
) -> dict:
    cleaned_question = question.strip()
    doc_count = collection_count()
    branch_filter = None if not branch or branch == "all" else branch

    if doc_count == 0:
        return {
            "answer": (
                "No guides are indexed yet. Run: python scripts/ingest_documents.py --reset "
                "to load public recruit guides, or upload PDFs from the sidebar."
            ),
            "sources": [],
            "masked": mask_sensitive,
            "document_count": 0,
            "intent": Intent.UNKNOWN.value,
            "branch": branch_filter or "all",
        }

    intent = classify_intent(cleaned_question)

    if is_out_of_scope(cleaned_question):
        return {
            "answer": build_out_of_scope_answer(),
            "sources": [],
            "masked": mask_sensitive,
            "document_count": doc_count,
            "intent": "out_of_scope",
            "branch": branch_filter or "all",
        }

    if intent in NO_RETRIEVAL_INTENTS:
        answer = build_answer_for_intent(intent, cleaned_question, [], doc_count)
        return {
            "answer": apply_answer_guardrails(cleaned_question, answer),
            "sources": [],
            "masked": mask_sensitive,
            "document_count": doc_count,
            "intent": intent.value,
            "branch": branch_filter or "all",
        }

    if is_vague_question(cleaned_question, intent):
        return {
            "answer": build_vague_answer(Intent.UNKNOWN),
            "sources": [],
            "masked": mask_sensitive,
            "document_count": doc_count,
            "intent": Intent.UNKNOWN.value,
            "branch": branch_filter or "all",
        }

    docs = _retrieve_documents(cleaned_question, intent, branch=branch_filter)

    if not docs:
        return {
            "answer": build_vague_answer(),
            "sources": [],
            "masked": mask_sensitive,
            "document_count": doc_count,
            "intent": intent.value,
            "branch": branch_filter or "all",
        }

    answer = build_answer_for_intent(intent, cleaned_question, docs, doc_count)

    if intent in {Intent.GENERAL, Intent.RECRUITING} and docs:
        context = "\n\n".join(doc.page_content for doc in docs[:3])
        answer = _maybe_enhance_with_llm(cleaned_question, context, answer)

    answer = apply_answer_guardrails(cleaned_question, answer)
    sources = mask_documents(docs[:3], enabled=mask_sensitive)

    return {
        "answer": answer,
        "sources": sources,
        "masked": mask_sensitive,
        "document_count": doc_count,
        "intent": intent.value,
        "branch": branch_filter or "all",
    }

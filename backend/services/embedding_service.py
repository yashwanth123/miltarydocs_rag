import os

from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain_community.llms import HuggingFacePipeline
from transformers import pipeline

from backend.utils.masking import mask_documents, mask_text
from backend.vector_store.chroma_client import collection_count, get_retriever

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "google/flan-t5-base")
SEARCH_K = int(os.getenv("SEARCH_K", "4"))

_generator = pipeline(
    "text2text-generation",
    model=LLM_MODEL,
    max_new_tokens=256,
    do_sample=False,
)
llm = HuggingFacePipeline(pipeline=_generator)

MILITARY_PROMPT_PREFIX = (
    "Answer the military document question using only the provided context. "
    "Be concise and factual. Question: "
)


def ask_question(question: str, mask_sensitive: bool = True) -> dict:
    if collection_count() == 0:
        return {
            "answer": (
                "No documents are indexed yet. Add PDFs to the data/ folder and run "
                "`python scripts/ingest_documents.py`."
            ),
            "sources": [],
            "masked": mask_sensitive,
            "document_count": 0,
        }

    retriever = get_retriever(search_k=SEARCH_K)
    docs = retriever.get_relevant_documents(question)
    context = "\n\n".join(doc.page_content for doc in docs)

    prompt = (
        f"Context:\n{context}\n\n"
        f"{MILITARY_PROMPT_PREFIX}{question}\nAnswer:"
    )

    try:
        raw_answer = llm.invoke(prompt).strip()
    except Exception as exc:
        raw_answer = f"Error generating answer: {exc}"

    sources = mask_documents(docs, enabled=mask_sensitive)
    answer = mask_text(raw_answer, enabled=mask_sensitive)

    return {
        "answer": answer,
        "sources": sources,
        "masked": mask_sensitive,
        "document_count": collection_count(),
    }

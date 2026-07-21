# MilitaryDocs RAG Chatbot

*Free, local document Q&A using LangChain, FastAPI, Hugging Face, and ChromaDB*

---

## Project overview

This project builds a document-based chatbot that retrieves answers from military PDF and text documents using:

- Retrieval-Augmented Generation (RAG)
- Hugging Face embeddings and LLM (no OpenAI or Pinecone required)
- ChromaDB for local vector search
- FastAPI backend with a built-in chat frontend
- Optional privacy masking for sensitive patterns in responses

---

## Project structure

```
miltarydocs_rag/
├── backend/
│   ├── api/
│   ├── services/
│   │   └── embedding_service.py
│   ├── utils/
│   │   ├── chunker.py
│   │   ├── masking.py
│   │   └── pdf_parser.py
│   ├── vector_store/
│   │   └── chroma_client.py
│   └── main.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── scripts/
│   ├── create_index.py
│   └── ingest_documents.py
├── data/
│   └── sample_chain_of_command.txt
├── requirements.txt
└── README.md
```

---

## Installation and setup

1. Clone the repository:

```bash
git clone <your-repo-url>
cd miltarydocs_rag
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env` (defaults work out of the box):

```env
CHROMA_PERSIST_DIR=chroma_db
CHROMA_COLLECTION=military-docs
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LLM_MODEL=google/flan-t5-base
SEARCH_K=4
```

4. Add documents to `data/` (PDF or TXT), then ingest:

```bash
export PYTHONPATH=.
python scripts/ingest_documents.py --reset
```

5. Start the server:

```bash
uvicorn backend.main:app --reload
```

6. Open the chat UI:

```
http://127.0.0.1:8000/
```

---

## API

### `GET /health`

Returns backend status and indexed chunk count.

### `POST /ask`

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the military chain of command?","mask_sensitive":true}'
```

Response:

```json
{
  "answer": "...",
  "sources": [{"content": "...", "source": "sample_chain_of_command.txt", "page": 1}],
  "masked": true,
  "document_count": 3
}
```

---

## Privacy masking

The frontend includes a toggle to mask sensitive patterns before display:

- Social Security numbers
- Email addresses
- Phone numbers
- Classification markings such as `SECRET`, `CONFIDENTIAL`, `UNCLASSIFIED//FOUO`

Masking applies to both the generated answer and retrieved source snippets. Turn it off in the sidebar when working with fully sanitized training data.

---

## What is configured

- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, local CPU)
- LLM: `google/flan-t5-base` (local, free)
- Vector store: ChromaDB persisted in `chroma_db/`
- PDF parsing: native text extraction with OCR fallback
- Frontend: responsive chat UI served from FastAPI

---

## Notes

- First run downloads Hugging Face models automatically.
- OCR requires Tesseract installed on your system for scanned PDFs.
- For stronger answers on capable hardware, set `LLM_MODEL` to a larger local model.
- No paid API keys are required for the default setup.

---

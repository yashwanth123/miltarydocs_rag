# Military Recruit Guide RAG

*Free, local military onboarding assistant using LangChain, FastAPI, Hugging Face, and ChromaDB*

---

## Project overview

Help people joining (or researching) the military find answers fast from **curated public guides** and uploaded documents:

- Joining steps, MEPS, ASVAB, benefits, ranks, and branch overviews
- Hybrid search (BM25 + vectors + reranker) for acronym-heavy queries
- Branch filter in the UI
- Fully local — no paid API keys required

---

## Quick start

```bash
git pull origin cursor/free-local-rag-frontend-947a
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.

# Load public recruit guides + any files in data/
python scripts/ingest_documents.py --reset

# Stable server (recommended)
bash scripts/run_server.sh
# Open http://127.0.0.1:8000/
```

---

## Public knowledge base

Pre-built guides live in `data/public/`:

```
data/public/
├── general/     joining, MEPS, ASVAB, ranks, benefits
├── army/
├── navy/
├── air-force/
├── marines/
├── coast-guard/
└── space-force/
```

Add your own PDFs/DOCX/TXT anywhere under `data/` and re-run ingest.

---

## Configuration (`.env`)

```env
USE_HYBRID_SEARCH=true
USE_RERANKER=true
USE_LLM=false
BM25_K=8
VECTOR_K=8
FINAL_K=4
```

---

## API

### `POST /ask`

```json
{
  "query": "How do I join the Army?",
  "branch": "army",
  "mask_sensitive": true
}
```

Branch values: `all`, `general`, `army`, `navy`, `air_force`, `marines`, `coast_guard`, `space_force`

---

## Disclaimer

Answers come from indexed public documents only. **Not official DoD guidance.** Verify enlistment, medical, and contract details with a qualified recruiter.

---

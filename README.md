# MilitaryDocs RAG Chatbot

*Question-Answering System Using LangChain, FastAPI, Hugging Face, and Pinecone*

---

## 📖 Project Overview

This project builds a document-based chatbot that retrieves relevant answers from military PDF documents using:

* ✅ Retrieval-Augmented Generation (RAG)
* ✅ Hugging Face LLM (No OpenAI dependency)
* ✅ Pinecone for vector search
* ✅ FastAPI backend

---

## 🗂️ Project Structure

```
miltarydocs_rag/
│
├── backend/
│   ├── api/                # FastAPI routes
│   │   └── main.py
│   ├── services/           # Query and embedding logic
│   │   └── embedding_service.py
│   ├── utils/              # PDF and text utilities
│   │   ├── chunker.py
│   │   └── pdf_parser.py
│   └── vector_store/       # Pinecone setup
│       └── pinecone_client.py
│
├── scripts/                # Setup scripts
│   ├── create_index.py
│   └── ingest_documents.py
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

1️⃣ Clone the repository:

```bash
git clone <your-repo-url>
cd miltarydocs_rag
```

2️⃣ Install dependencies:

```bash
pip install -r requirements.txt
```

3️⃣ Configure your environment variables:

Create a `.env` file:

```
HUGGINGFACEHUB_API_TOKEN=your_hf_token_here
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_ENV=us-east-1
```

4️⃣ Create Pinecone index and ingest documents:

```bash
export PYTHONPATH=.
python scripts/create_index.py
python scripts/ingest_documents.py
```

5️⃣ Run the FastAPI server:

```bash
uvicorn backend.main:app --reload
```

6️⃣ Test the API:

Visit:

```
http://127.0.0.1:8000/docs
```

Example `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
-H "Content-Type: application/json" \
-d '{"query":"What is the military chain of command?"}'
```

---

## ✅ What’s Configured:

* Hugging Face Embeddings → `sentence-transformers/all-MiniLM-L6-v2`
* Hugging Face LLM → Configurable via `.env`
* Pinecone vector database with 384 dimensions
* PDF text + OCR extraction
* FastAPI endpoint: `/ask`

---

## ✍️ Notes

* Tested on Python 3.13
* Hugging Face token is required for private/public LLM access
* If facing version warnings:
  Install:

  ```bash
  pip install -U langchain langchain-community huggingface-hub
  ```

---

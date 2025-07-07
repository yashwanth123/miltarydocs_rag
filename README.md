# 🪖 MilitaryDocs RAG

**MilitaryDocs RAG** is a Retrieval-Augmented Generation (RAG) application built using **FastAPI**, **Pinecone**, **OpenAI**, and **LangChain**, designed to allow semantic search and question answering over large collections of scanned military documents (PDFs).

---

## 🚀 Features

- ✅ Ingests scanned PDFs with OCR (Tesseract + PyMuPDF)
- ✅ Extracts text and splits into context-aware chunks
- ✅ Stores vector embeddings in **Pinecone**
- ✅ Retrieves relevant document chunks using LangChain retriever
- ✅ Uses GPT-4 (or Claude) to generate answers grounded in PDF content
- ✅ Exposed via a **FastAPI backend** and a basic **HTML frontend**

---

## 📁 Project Structure

```bash
miltarydocs_rag/
├── backend/
│   ├── api/
│   │   └── endpoints.py         # API routes
│   ├── services/
│   │   └── embedding_service.py # Main query logic
│   ├── utils/
│   │   ├── chunker.py           # Text chunking
│   │   └── pdf_parser.py        # OCR + PDF parsing
│   ├── vector_store/
│   │   └── pinecone_client.py   # Pinecone vector DB integration
│   └── main.py                  # FastAPI entrypoint
├── scripts/
│   └── ingest_documents.py      # Script to process + embed PDFs
├── data/                        # Place your PDFs here
├── .env                         # API keys and configs
└── requirements.txt


🔧 Setup Instructions
1. Clone & Set Up Environment
git clone https://github.com/yourusername/militarydocs_rag.git
cd militarydocs_rag
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

2. Install OCR Dependencies
brew install poppler tesseract

3. Create .env File
OPENAI_API_KEY=sk-xxxx
PINECONE_API_KEY=pcsk-xxxx
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX=military-docs

📥 Ingest PDFs (with OCR)
Place your scanned or native PDFs inside data/, e.g.:


data/pdf1.pdf
data/manual_2024.pdf

Run ingestion:
export PYTHONPATH=.
python scripts/ingest_documents.py

🌐 Start the API Server
uvicorn backend.main:app --reload
Then open: http://127.0.0.1:8000/docs

🧠 How It Works (RAG Flow)
OCR with PyMuPDF + Tesseract → extracts clean text from scanned PDFs

Text Chunking → splits long documents into semantic blocks

Embedding → uses OpenAI's embedding model (text-embedding-3-small)

Pinecone → stores and indexes embeddings for similarity search

LangChain Retriever → pulls relevant chunks for any user query

LLM → GPT-4 (or Claude) generates a grounded response

FastAPI Endpoint → delivers results via REST API

✅ Example API Usage
POST /ask

json
Copy
Edit
{
  "query": "What are the procedures for emergency deployment?",
  "top_k": 5
}
Response:

json
Copy
Edit
{
  "answer": "According to the manual, emergency deployment involves..."
}
📈 Next Steps
Task	Status
✅ OCR for scanned PDFs	Done
✅ FastAPI backend with query endpoint	Done
✅ Pinecone + OpenAI integration	Done
❌ Switch to HuggingFace embeddings (optional)	🔜
❌ Web frontend (HTML input + results)	🔜
❌ Auth & document upload portal (multi-user)	🔜
❌ Cost monitoring & rate-limit handling	🔜
❌ Deploy to Render / EC2	🔜

💡 Tips
Want to avoid OpenAI costs while developing? Swap embeddings for all-MiniLM-L6-v2 from HuggingFace (I can help you do this).

Use tiktoken to estimate chunk token lengths for better LLM context handling.

Consider replacing deprecated LangchainPinecone with PineconeVectorStore.

🤝 Credits
Built with ❤️ using:

FastAPI

LangChain

OpenAI

Pinecone

pdfminer.six

PyMuPDF (fitz)

Tesseract OCR

📬 Contact
Yashwanth Sai Tirukkovalluru
Feel free to open issues or contact for deployment & scaling help.



# miltarydocs_rag

# 🪖 MilitaryDocs-RAG: Document Chatbot with Vector Search

MilitaryDocs-RAG is a Retrieval-Augmented Generation (RAG) application that allows users to query over thousands of military PDF documents efficiently using vector embeddings and a conversational AI interface. Built with FastAPI, LangChain, Pinecone, and OpenAI, this system supports intelligent retrieval of domain-specific information from over 2500 PDF files.

---

## 🚀 Features

- 🔍 **Semantic Search** over 2500+ military PDFs using vector databases
- 🧠 **RAG-based Chatbot** powered by OpenAI (GPT-4)
- 🗂️ **Metadata-aware Retrieval** (e.g. section numbers, scope questions, requirement-specific queries)
- ⚡ **FastAPI backend** with API endpoints ready for integration
- 📦 Modular architecture with support for scalable ingestion and storage
- 🔐 Configurable with `.env` for API keys and secrets

---

## 📁 Project Structure

miltarydocs_rag/
├── backend/
│ ├── api/ # FastAPI endpoints
│ ├── services/ # Embedding + QA logic
│ ├── utils/ # Helper functions
│ ├── vector_store/ # Pinecone or Chroma DB clients
│ └── main.py # FastAPI app entrypoint
├── scripts/
│ └── ingest_documents.py # PDF chunking + embedding ingestion
├── data/
│ └── pdfs/ # Directory for raw PDF files
├── .env # API keys (not checked into git)
├── requirements.txt # All required pip packages
└── README.md # You’re here

yaml
Copy
Edit

---

## ⚙️ Setup Instructions

1. **Clone this repo**  
   ```bash
   git clone https://github.com/yourusername/militarydocs_rag.git
   cd militarydocs_rag
Create a virtual environment

bash
Copy
Edit
python3 -m venv venv
source venv/bin/activate
Install dependencies

bash
Copy
Edit
pip install -r requirements.txt
Add your environment variables to .env

ini
Copy
Edit
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENV=your_pinecone_environment
PINECONE_INDEX_NAME=your_index_name
Ingest documents
Put all your PDFs in data/pdfs/ then run:

bash
Copy
Edit
python scripts/ingest_documents.py
Run FastAPI server

bash
Copy
Edit
uvicorn backend.main:app --reload
🧪 Example Queries
✅ “What is the scope of this document?”
✅ “Tell me about section 1.2.2”
✅ “Write me an inspection plan for requirement 2.3.3”

🔐 Security Notes
This system is designed for internal use with potentially sensitive military documentation. Ensure proper:

Access controls

Data encryption (at rest and in transit)

Secure API key management (.env)

Role-based access for endpoints (future feature)

🧠 Future Improvements
Add user feedback and rating loop

Integrate local fallback LLM

UI frontend with chat interface

Document summarization per section

Hybrid routing (general vs. specific query detection)

👨‍💻 Contributors
Yashwanth Sai Tirukkovalluru
Max Filder

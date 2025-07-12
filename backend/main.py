import os
from dotenv import load_dotenv

# Load .env from project root manually (to work during uvicorn reload)
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
print("🔍 Loading .env from:", env_path)
load_dotenv(dotenv_path=env_path)

# DEBUG: Show values loaded
print("🔑 PINECONE_API_KEY =", os.getenv("PINECONE_API_KEY"))
print("🌎 PINECONE_ENVIRONMENT =", os.getenv("PINECONE_ENVIRONMENT"))
print("📚 PINECONE_INDEX =", os.getenv("PINECONE_INDEX"))
print("🧠 OPENAI_API_KEY =", os.getenv("OPENAI_API_KEY"))

# FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import endpoints

app = FastAPI(
    title="MilitaryDocs RAG API",
    description="FastAPI backend for querying military documents using Pinecone and OpenAI.",
    version="1.0.0",
)

# Enable CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or replace with frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your API endpoints
app.include_router(endpoints.router)

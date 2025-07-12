import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import Pinecone as LangchainPinecone

# Load env vars
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")  # e.g., "us-east-1"
PINECONE_INDEX = os.getenv("PINECONE_INDEX")  # e.g., "military-docs-index"

if not all([PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX]):
    raise ValueError("Missing one of: PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX")

# ✅ New SDK usage
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if not exists
if PINECONE_INDEX not in pc.list_indexes().names():
    print(f"⚠️ Index '{PINECONE_INDEX}' not found. Creating it...")
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT)
    )
    print(f"✅ Created index: {PINECONE_INDEX}")
else:
    print(f"📚 Using existing index: {PINECONE_INDEX}")

# Connect to index
index = pc.Index(PINECONE_INDEX)
embed_model = OpenAIEmbeddings()

# Vector store used in LangChain
vector_store = LangchainPinecone(index=index, embedding=embed_model, text_key="text")

# Ingest helper function
def add_to_index(texts):
    print(f"📥 Adding {len(texts)} chunks to Pinecone...")
    vector_store.add_documents(texts)
    print("✅ Ingestion complete.")

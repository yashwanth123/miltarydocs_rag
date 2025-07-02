from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone as LangChainPinecone

load_dotenv()

pinecone_api_key = os.getenv("PINECONE_API_KEY")
index_name = os.getenv("PINECONE_INDEX_NAME")
environment = os.getenv("PINECONE_ENV")

# Initialize Pinecone
pc = Pinecone(api_key=pinecone_api_key)

# Create index if it doesn't exist
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=environment)
    )

index = pc.Index(index_name)

# Embedding model
embedding = OpenAIEmbeddings()

# Vector store
vector_store = LangChainPinecone(index, embedding.embed_query, "text")

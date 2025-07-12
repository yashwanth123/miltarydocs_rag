# scripts/create_index.py
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

api_key = os.environ["PINECONE_API_KEY"]
index_name = os.environ["PINECONE_INDEX"]
region = os.environ["PINECONE_ENVIRONMENT"]
cloud = os.environ["PINECONE_CLOUD"]

pc = Pinecone(api_key=api_key)

if index_name in [i["name"] for i in pc.list_indexes()]:
    print("⚠️ Deleting stale index...")
    pc.delete_index(index_name)

print(f"✅ Creating fresh index in {cloud}/{region}...")
pc.create_index(
    name=index_name,
    dimension=1536,
    metric="cosine",
    spec=ServerlessSpec(cloud=cloud, region=region)
)
print("🎉 Index created successfully.")

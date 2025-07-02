from backend.vector_store.pinecone_client import vector_store


def ask_question(query: str):
    results = vector_store.similarity_search(query, k=5)
    return [doc.page_content for doc in results]

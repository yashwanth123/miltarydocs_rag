from backend.vector_store.pinecone_client import vector_store
from langchain_openai import OpenAI
from langchain.chains import RetrievalQA

# Load LLM
llm = OpenAI(model_name="gpt-4", temperature=0.3)

# Retrieval Chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=False
)

def ask_question(question: str) -> str:
    try:
        response = qa_chain.run(question)
        return response
    except Exception as e:
        return f"❌ Error during query: {str(e)}"

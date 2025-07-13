from transformers import pipeline
from langchain.llms import HuggingFacePipeline

from backend.vector_store.pinecone_client import vector_store
from langchain.chains import RetrievalQA

pipe = pipeline("text2text-generation", model="google/flan-t5-base")

llm = HuggingFacePipeline(pipeline=pipe)

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

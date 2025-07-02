from backend.vector_store.pinecone_client import vector_store
from backend.utils.pdf_parser import load_pdf
from backend.utils.chunker import split_text
from langchain.docstore.document import Document
import os


DATA_PATH = "./data"


def ingest():
    for file in os.listdir(DATA_PATH):
        if file.endswith(".pdf"):
            file_path = os.path.join(DATA_PATH, file)
            text = load_pdf(file_path)
            chunks = split_text(text)
            docs = [Document(page_content=chunk, metadata={"source": file}) for chunk in chunks]
            vector_store.add_documents(docs)
            print(f"✅ {file} ingested")


if __name__ == "__main__":
    ingest()

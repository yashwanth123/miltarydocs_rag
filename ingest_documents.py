from backend.utils.pdf_parser import extract_text_from_pdf
from backend.utils.chunker import chunk_text
from backend.vector_store.pinecone_client import add_to_index
from langchain_core.documents import Document

import os

PDF_FOLDER = "data"  # Make sure this exists and has PDFs

all_docs = []

for filename in os.listdir(PDF_FOLDER):
    if filename.endswith(".pdf"):
        file_path = os.path.join(PDF_FOLDER, filename)
        print(f"🔍 Processing: {filename}")
        text = extract_text_from_pdf(file_path)
        chunks = chunk_text(text)
        docs = [Document(page_content=str(chunk), metadata={"source": filename}) for chunk in chunks if isinstance(chunk, str) and chunk.strip()]

        all_docs.extend(docs)

# Store into Pinecone
add_to_index(all_docs)

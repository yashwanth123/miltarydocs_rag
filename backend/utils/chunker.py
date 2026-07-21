from langchain.text_splitter import RecursiveCharacterTextSplitter


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    if not text or not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)

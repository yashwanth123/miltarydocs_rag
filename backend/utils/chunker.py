import re

from langchain.text_splitter import RecursiveCharacterTextSplitter


def _split_sections(text: str) -> list[str]:
    lines = text.splitlines()
    sections: list[str] = []
    current: list[str] = []

    for line in lines:
        if re.match(r"^#{1,3}\s+", line) or re.match(r"^[A-Z][A-Z0-9 /-]{4,}$", line.strip()):
            if current:
                sections.append("\n".join(current).strip())
                current = []
        current.append(line)

    if current:
        sections.append("\n".join(current).strip())

    return [section for section in sections if section.strip()]


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    if not text or not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    sections = _split_sections(text)
    if not sections:
        sections = [text.strip()]

    chunks: list[str] = []
    for section in sections:
        if len(section) <= chunk_size:
            chunks.append(section)
            continue
        chunks.extend(splitter.split_text(section))

    return [chunk.strip() for chunk in chunks if chunk.strip()]

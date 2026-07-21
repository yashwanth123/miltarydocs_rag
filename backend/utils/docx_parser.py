from pathlib import Path

from docx import Document as DocxDocument


def extract_text_from_docx(docx_path: str) -> list[tuple[int, str]]:
    doc = DocxDocument(docx_path)
    paragraphs = [paragraph.text.strip() for paragraph in doc.paragraphs if paragraph.text.strip()]

    if not paragraphs:
        return []

    return [(1, "\n".join(paragraphs))]

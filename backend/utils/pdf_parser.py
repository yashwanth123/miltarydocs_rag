from pypdf import PdfReader


def extract_text_from_pdf(pdf_path: str) -> list[tuple[int, str]]:
    pages: list[tuple[int, str]] = []
    reader = PdfReader(pdf_path)

    for page_num, page in enumerate(reader.pages, start=1):
        page_text = (page.extract_text() or "").strip()
        if page_text:
            pages.append((page_num, page_text))

    if not pages:
        print(
            f"Warning: no text extracted from {pdf_path}. "
            "If this is a scanned PDF, export it as searchable text first."
        )

    return pages

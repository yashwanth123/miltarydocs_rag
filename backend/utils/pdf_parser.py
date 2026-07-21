import io

import fitz
import pytesseract
from PIL import Image


def extract_text_from_pdf(pdf_path: str) -> list[tuple[int, str]]:
    pages: list[tuple[int, str]] = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_text = page.get_text("text").strip()

        if len(page_text) < 40:
            print(f"OCR fallback for page {page_num + 1} in {pdf_path}")
            pix = page.get_pixmap()
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            try:
                page_text = pytesseract.image_to_string(image).strip()
            except Exception as exc:
                print(f"OCR failed on page {page_num + 1}: {exc}")
                page_text = ""

        if page_text:
            pages.append((page_num + 1, page_text))

    doc.close()
    return pages

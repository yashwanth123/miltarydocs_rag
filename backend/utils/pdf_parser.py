import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        print(f"🧠 OCR on page {page_num + 1}")
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        image = Image.open(io.BytesIO(pix.tobytes("png")))

        try:
            page_text = pytesseract.image_to_string(image)
            if page_text.strip():
                text += page_text + "\n"
        except Exception as e:
            print(f"❌ OCR failed on page {page_num + 1}: {e}")

    return text

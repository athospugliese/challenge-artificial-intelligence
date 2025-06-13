from .base_processor import BaseProcessor
import pymupdf
from io import BytesIO

class PDFProcessor(BaseProcessor):
    def process(self, file_content: bytes) -> str:
        try:
            doc = pymupdf.open(stream=file_content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"Erro ao extrair texto do PDF: {e}")
            return ""



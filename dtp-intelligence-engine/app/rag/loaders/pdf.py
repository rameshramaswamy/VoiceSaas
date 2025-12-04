from pypdf import PdfReader
from io import BytesIO
from typing import Optional

class PDFLoader:
    @staticmethod
    def extract_text(file_content: bytes) -> str:
        """
        Parses raw PDF bytes into a single string.
        """
        try:
            reader = PdfReader(BytesIO(file_content))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")
from pypdf import PdfReader
from docx import Document


class ParserService:

    @staticmethod
    def extract_pdf_text(file_path: str) -> str:

        reader = PdfReader(file_path)

        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

        return text

    @staticmethod
    def extract_docx_text(file_path: str) -> str:

        document = Document(file_path)

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

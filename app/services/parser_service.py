from pypdf import PdfReader


class ParserService:

    @staticmethod
    def extract_pdf_text(file_path: str) -> str:

        reader = PdfReader(file_path)

        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

        return text
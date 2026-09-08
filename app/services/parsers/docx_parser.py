from docx import Document


class DOCXParser:

    @staticmethod
    def extract_text(file_path: str) -> str:

        document = Document(file_path)

        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

        return text
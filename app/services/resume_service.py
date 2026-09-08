from pathlib import Path
import shutil
import uuid

from fastapi import UploadFile

from app.services.parser_service import ParserService
from app.core.constants import ALLOWED_EXTENSIONS


UPLOAD_DIR = Path("uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ResumeService:

    @staticmethod
    def upload_resume(file: UploadFile):

        extension = Path(file.filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError(
                "Only PDF and DOCX files are allowed"
            )

        unique_name = f"{uuid.uuid4()}{extension}"

        file_path = UPLOAD_DIR / unique_name

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        if extension == ".pdf":
            resume_text = ParserService.extract_pdf_text(
                str(file_path)
            )
        else:
            resume_text = ParserService.extract_docx_text(
                str(file_path)
            )

        return {
            "id": 1,
            "file_name": file.filename,
            "file_path": str(file_path),
            "uploaded_at": "2026-09-08T00:00:00",
        }
from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.db.dependencies import get_db

from app.services.resume_service import ResumeService
from app.services.extraction_service import ExtractionService

from app.services.parsers.pdf_parser import PDFParser
from app.services.parsers.docx_parser import DOCXParser

from app.schemas.resume import ResumeResponse
from app.schemas.resume import ParsedResumeResponse

from app.schemas.candidate import CandidateExtractResponse

router = APIRouter()


@router.post(
    "/parse",
    response_model=ParsedResumeResponse
)
async def parse_resume(
    file: UploadFile = File(...)
):

    file_bytes = await file.read()

    temp_path = f"uploads/{file.filename}"

    with open(temp_path, "wb") as buffer:
        buffer.write(file_bytes)

    if file.filename.endswith(".pdf"):
        text = PDFParser.extract_text(
            temp_path
        )

    elif file.filename.endswith(".docx"):
        text = DOCXParser.extract_text(
            temp_path
        )

    else:
        text = "Unsupported file type"

    return {
        "filename": file.filename,
        "extracted_text": text
    }


@router.post(
    "/upload",
    response_model=ResumeResponse
)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    try:
        return ResumeService.upload_resume(file)

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post(
    "/extract",
    response_model=CandidateExtractResponse
)
async def extract_candidate(
    file: UploadFile = File(...)
):

    file_bytes = await file.read()

    temp_path = f"uploads/{file.filename}"

    with open(temp_path, "wb") as buffer:
        buffer.write(file_bytes)

    if file.filename.endswith(".pdf"):

        text = PDFParser.extract_text(
            temp_path
        )

    elif file.filename.endswith(".docx"):

        text = DOCXParser.extract_text(
            temp_path
        )

    else:

        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX supported"
        )

    return {
    "name": ExtractionService.extract_name(text),
    "email": ExtractionService.extract_email(text),
    "phone": ExtractionService.extract_phone(text),
    "skills": ExtractionService.extract_skills(text)
}
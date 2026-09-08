from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.db.dependencies import get_db

from app.services.resume_service import (
    ResumeService
)

from app.schemas.resume import (
    ResumeResponse
)
from app.services.parsers.pdf_parser import PDFParser
from app.services.parsers.docx_parser import DOCXParser
from app.schemas.resume import ParsedResumeResponse

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
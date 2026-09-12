from pathlib import Path
import uuid

from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import HTTPException
from fastapi import Depends
from fastapi import Response
from fastapi import status

from sqlalchemy.orm import Session

from app.db.dependencies import get_db

from app.services.extraction_service import ExtractionService
from app.services.candidate_service import CandidateService

from app.services.parsers.pdf_parser import PDFParser
from app.services.parsers.docx_parser import DOCXParser

from app.schemas.candidate import CandidateUploadResponse
from app.core.constants import ALLOWED_EXTENSIONS

router = APIRouter()
UPLOAD_DIR = Path("uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "/extract",
    response_model=CandidateUploadResponse,
    status_code=status.HTTP_201_CREATED
)
async def extract_candidate(
    response: Response,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )

    temp_path = UPLOAD_DIR / f"{uuid.uuid4()}{extension}"

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )

    with open(temp_path, "wb") as buffer:
        buffer.write(file_bytes)

    try:
        if extension == ".pdf":
            text = PDFParser.extract_text(str(temp_path))
        else:
            text = DOCXParser.extract_text(str(temp_path))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not parse uploaded resume"
        ) from exc

    name = ExtractionService.extract_name(text)

    email = ExtractionService.extract_email(text)

    phone = ExtractionService.extract_phone(text)

    skills = ExtractionService.extract_skills(text)

    candidate_result = CandidateService.create_candidate(
        db=db,
        name=name,
        email=email,
        phone=phone,
        skills=skills,
        resume_path=str(temp_path)
    )

    if not candidate_result["created"]:
        if not candidate_result["candidate"]:
            raise HTTPException(
                status_code=candidate_result["status_code"],
                detail=candidate_result["message"]
            )

        response.status_code = status.HTTP_200_OK

        return {
            "created": False,
            "message": candidate_result["message"],
            "candidate": CandidateService._serialize_candidate(
                candidate_result["candidate"]
            )
        }

    return {
        "created": True,
        "message": candidate_result["message"],
        "candidate": CandidateService._serialize_candidate(
            candidate_result["candidate"]
        )
    }

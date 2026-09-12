from pathlib import Path
import uuid

from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import HTTPException
from fastapi import status
from fastapi import Depends

from sqlalchemy.orm import Session

from app.db.dependencies import get_db

from app.schemas.job import (
    JobCreate,
    JobExtractResponse,
    JobResponse,
    JobUpdate
)

from app.services.job_service import (
    JobService
)

from app.services.matching_service import (
    MatchingService
)
from app.services.candidate_service import CandidateService

from app.services.parsers.pdf_parser import (
    PDFParser
)
from app.services.parsers.docx_parser import DOCXParser
from app.core.constants import ALLOWED_EXTENSIONS
from app.schemas.match import (
    CandidateJobMatchResponse,
    JobCandidateMatchRequest
)

router = APIRouter()
UPLOAD_DIR = Path("uploads/jobs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED
)
def create_job(
    job: JobCreate,
    db: Session = Depends(get_db)
):
    return JobService.create(
        db,
        job
    )


@router.get(
    "/",
    response_model=list[JobResponse]
)
def get_jobs(
    db: Session = Depends(get_db)
):
    return JobService.get_all(db)


@router.get(
    "/{job_id}/candidates",
    response_model=list[CandidateJobMatchResponse]
)
def rank_candidates_for_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = JobService.get_by_id(
        db,
        job_id
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return MatchingService.rank_candidates_for_job(
        CandidateService.get_all_models(db),
        job
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = JobService.get_by_id(
        db,
        job_id
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return job


@router.patch(
    "/{job_id}",
    response_model=JobResponse
)
def update_job(
    job_id: int,
    job: JobUpdate,
    db: Session = Depends(get_db)
):
    updated_job = JobService.update(
        db,
        job_id,
        job
    )

    if not updated_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return updated_job


@router.put(
    "/{job_id}",
    response_model=JobResponse
)
def replace_job(
    job_id: int,
    job: JobUpdate,
    db: Session = Depends(get_db)
):
    return update_job(
        job_id,
        job,
        db
    )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    deleted = JobService.delete(
        db,
        job_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )


@router.post(
    "/extract",
    response_model=JobExtractResponse,
    status_code=status.HTTP_201_CREATED
)
async def extract_job(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )

    temp_path = UPLOAD_DIR / f"{uuid.uuid4()}{extension}"

    with open(
        temp_path,
        "wb"
    ) as buffer:

        buffer.write(
            file_bytes
        )

    try:
        if extension == ".pdf":
            text = PDFParser.extract_text(str(temp_path))
        else:
            text = DOCXParser.extract_text(str(temp_path))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not parse uploaded job description"
        ) from exc

    return JobService.create_from_text(
        db=db,
        title=Path(file.filename or "Untitled Job").stem,
        text=text
    )


@router.post(
    "/match",
    response_model=list[CandidateJobMatchResponse]
)
async def match_job(
    match_request: JobCandidateMatchRequest,
    db: Session = Depends(get_db)
):
    job = JobService.get_by_id(
        db,
        match_request.job_id
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return MatchingService.rank_candidates_for_job(
        CandidateService.get_all_models(db),
        job
    )

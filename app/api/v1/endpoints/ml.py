from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.ml import (
    RankingDatasetRecord,
    RankingModelStatusResponse,
    RankingTrainingResponse,
)
from app.services.ranking_model_service import RankingModelService

router = APIRouter()


@router.get("/ranking/status", response_model=RankingModelStatusResponse)
def get_ranking_model_status():
    return RankingModelService.status()


@router.get("/ranking/dataset", response_model=list[RankingDatasetRecord])
def get_ranking_dataset(db: Session = Depends(get_db)):
    return RankingModelService.dataset_records(db)


@router.post("/ranking/train", response_model=RankingTrainingResponse)
def train_ranking_model(db: Session = Depends(get_db)):
    try:
        return RankingModelService.train(db)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

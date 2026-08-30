from fastapi import APIRouter, Depends, File, Query, UploadFile, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.core.db import get_db
from app.schemas.dataset import DatasetListResponse, DatasetRead, DatasetUpdate, DatasetPreviewResponse
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])

# 上傳資料集
@router.post("/upload", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    service = DatasetService(db)
    return service.upload_dataset(file)

# 列出資料集
@router.get("", response_model=DatasetListResponse)
def list_datasets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = DatasetService(db)
    return service.list_datasets(page=page, page_size=page_size)

# 取得資料集
@router.get("/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    service = DatasetService(db)
    return service.get_dataset(dataset_id)

# 更新資料集
@router.patch("/{dataset_id}", response_model=DatasetRead)
def update_dataset(dataset_id: int, payload: DatasetUpdate, db: Session = Depends(get_db)):
    service = DatasetService(db)
    return service.update_dataset(dataset_id, payload)

# 刪除資料集
@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    service = DatasetService(db)
    service.delete_dataset(dataset_id)

# 取得資料集預覽資料
@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def get_dataset_preview(
    dataset_id: int, 
    limit: int = Query(default=100, ge=1, le=2000), 
    db: Session = Depends(get_db)
):
    service = DatasetService(db)
    return service.get_dataset_preview(dataset_id, limit=limit)

# 下載資料集
@router.get("/{dataset_id}/download")
def download_dataset(dataset_id: int, db: Session = Depends(get_db)):
    service = DatasetService(db)
    dataset = service.get_dataset(dataset_id)
    if not dataset or not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")
    return FileResponse(dataset.file_path, filename=dataset.filename)

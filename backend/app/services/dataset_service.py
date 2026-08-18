from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.dataset import Dataset, DatasetColumn
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.dataset import DatasetListResponse, DatasetRead, DatasetUpdate


class DatasetService:
    def __init__(self, db: Session):
        self.repo = DatasetRepository(db)
        self.upload_root = Path(__file__).resolve().parents[2] / "uploads"
        self.upload_root.mkdir(parents=True, exist_ok=True)

    # 上傳資料集
    def upload_dataset(self, file: UploadFile) -> DatasetRead:
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File name is required")

        suffix = Path(file.filename).suffix.lower()
        if suffix not in {".csv", ".xlsx", ".xls"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV/XLSX/XLS files are supported",
            )

        saved_name = f"{uuid4().hex}{suffix}"
        saved_path = self.upload_root / saved_name
        file_bytes = file.file.read()
        saved_path.write_bytes(file_bytes)

        try:
            if suffix == ".csv":
                dataframe = pd.read_csv(saved_path)
            else:
                dataframe = pd.read_excel(saved_path)
        except Exception as exc:
            saved_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to parse file: {exc}",
            ) from exc

        dataset = Dataset(
            filename=file.filename,
            file_path=str(Path("uploads") / saved_name),
            row_count=int(dataframe.shape[0]),
            column_count=int(dataframe.shape[1]),
            status="ready",
        )

        for column in dataframe.columns:
            series = dataframe[column]
            if pd.api.types.is_numeric_dtype(series):
                detected_type = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(series):
                detected_type = "datetime"
            else:
                detected_type = "categorical"

            dataset.columns.append(
                DatasetColumn(
                    column_name=str(column),
                    data_type=detected_type,
                    null_count=int(series.isna().sum()),
                    unique_count=int(series.nunique(dropna=True)),
                )
            )

        created = self.repo.create(dataset)
        return DatasetRead.model_validate(created)

    # 列出資料集
    def list_datasets(self, page: int, page_size: int) -> DatasetListResponse:
        items, total = self.repo.list(page=page, page_size=page_size)
        return DatasetListResponse(
            items=[DatasetRead.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    # 取得資料集
    def get_dataset(self, dataset_id: int) -> DatasetRead:
        dataset = self.repo.get(dataset_id)
        if not dataset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
        return DatasetRead.model_validate(dataset)

    # 更新資料集
    def update_dataset(self, dataset_id: int, payload: DatasetUpdate) -> DatasetRead:
        dataset = self.repo.get(dataset_id)
        if not dataset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

        if payload.status is not None:
            dataset.status = payload.status
        if payload.filename is not None:
            dataset.filename = payload.filename

        updated = self.repo.update(dataset)
        return DatasetRead.model_validate(updated)
    
    # 刪除資料集
    def delete_dataset(self, dataset_id: int) -> None:
        dataset = self.repo.get(dataset_id)
        if not dataset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

        saved_path = Path(__file__).resolve().parents[2] / dataset.file_path
        self.repo.delete(dataset)
        saved_path.unlink(missing_ok=True)

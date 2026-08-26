import logging
import functools
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import UPLOAD_ROOT
from app.models.dataset import Dataset, DatasetColumn
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.dataset import DatasetListResponse, DatasetPreviewResponse, DatasetRead, DatasetUpdate

logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB


@functools.lru_cache(maxsize=32)
def _read_preview_df(saved_path_str: str, limit: int) -> pd.DataFrame:
    path_obj = Path(saved_path_str)
    suffix = path_obj.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path_obj, nrows=limit)
    else:
        return pd.read_excel(path_obj, nrows=limit)


class DatasetService:
    def __init__(self, db: Session):
        self.repo = DatasetRepository(db)
        self.upload_root = UPLOAD_ROOT
        self.upload_root.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, file_path: str) -> Path:
        """將 DB 中的相對路徑解析為絕對路徑，並驗證其確實位於 upload_root 之下，
        防止 Path Traversal 攻擊（例如 file_path = '../../etc/passwd'）。"""
        resolved = (self.upload_root / file_path).resolve()
        if not resolved.is_relative_to(self.upload_root.resolve()):
            logger.warning("偵測到可疑的 Path Traversal 嘗試：file_path=%s", file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path",
            )
        return resolved

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
        if len(file_bytes) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File too large. Maximum allowed size is {MAX_UPLOAD_SIZE // (1024 * 1024)} MB",
            )
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
            file_path=saved_name,
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

        saved_path = self._resolve_safe_path(dataset.file_path)

        # 先刪 DB 紀錄（在 transaction 內），commit 成功後才刪實體檔案。
        # 若 DB 刪除因外鍵約束等原因失敗，transaction 會 rollback，
        # 此時檔案尚未被刪除，可確保資料一致性。
        try:
            self.repo.delete(dataset)
        except Exception as e:
            logger.error("刪除資料集 %d 的 DB 紀錄失敗：%s", dataset_id, e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="刪除失敗，該資料集可能有關聯的分析任務，請先刪除相關任務後再試。",
            )

        # DB commit 成功後再刪實體檔案；刪除失敗不影響 API 回應，
        # 殘留的孤兒檔案可透過後台排程清理。
        try:
            saved_path.unlink(missing_ok=True)
        except OSError as e:
            logger.warning("資料集 %d 的實體檔案刪除失敗（孤兒檔案）：%s", dataset_id, e)

    # 取得資料集預覽資料
    def get_dataset_preview(self, dataset_id: int, limit: int = 100) -> DatasetPreviewResponse:
        dataset = self.repo.get(dataset_id)
        if not dataset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

        # 使用安全路徑解析，防止 Path Traversal
        saved_path = self._resolve_safe_path(dataset.file_path)
        if not saved_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset file not found on disk")

        suffix = saved_path.suffix.lower()
        try:
            df = _read_preview_df(str(saved_path), limit)
        except Exception as exc:
            logger.error("讀取資料集 %d 檔案失敗：%s", dataset_id, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="讀取資料集失敗，請確認檔案格式是否正確。",
            )

        # Replace NaN with None so it's valid JSON for the frontend
        df = df.where(pd.notnull(df), None)
        columns = df.columns.astype(str).tolist()
        data = df.to_dict(orient="records")

        return DatasetPreviewResponse(columns=columns, data=data)

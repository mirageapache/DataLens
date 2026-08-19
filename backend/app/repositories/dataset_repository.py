from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.dataset import Dataset


class DatasetRepository:
    def __init__(self, db: Session):
        self.db = db

    # 建立資料集
    def create(self, dataset: Dataset) -> Dataset:
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    # 取得資料集
    def get(self, dataset_id: int) -> Dataset | None:
        stmt = (
            select(Dataset)
            .options(selectinload(Dataset.columns))
            .where(Dataset.id == dataset_id)
        )
        return self.db.scalar(stmt)

    # 列出資料集
    def list(self, page: int, page_size: int) -> tuple[list[Dataset], int]:
        offset = (page - 1) * page_size

        stmt = (
            select(Dataset)
            .options(selectinload(Dataset.columns))
            .order_by(Dataset.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(self.db.scalars(stmt))
        total = self.db.scalar(select(func.count()).select_from(Dataset)) or 0
        return items, total

    # 更新資料集
    def update(self, dataset: Dataset) -> Dataset:
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    # 刪除資料集
    def delete(self, dataset: Dataset) -> None:
        self.db.delete(dataset)
        self.db.commit()

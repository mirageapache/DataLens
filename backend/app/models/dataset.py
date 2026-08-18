import datetime as dt

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str]
    file_path: Mapped[str]
    row_count: Mapped[int | None]
    column_count: Mapped[int | None]
    status: Mapped[str] = mapped_column(default="uploaded")  # uploaded/processing/ready/failed
    created_at: Mapped[dt.datetime] = mapped_column(server_default=func.now())

    columns: Mapped[list["DatasetColumn"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )


class DatasetColumn(Base):
    __tablename__ = "dataset_columns"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))
    column_name: Mapped[str]
    data_type: Mapped[str]        # numeric/categorical/datetime
    null_count: Mapped[int | None]
    unique_count: Mapped[int | None]

    dataset: Mapped["Dataset"] = relationship(back_populates="columns")

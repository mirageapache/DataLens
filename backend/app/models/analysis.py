import datetime as dt
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))
    task_type: Mapped[str]  # e.g., "descriptive", "correlation", "group_by", "time_series"
    celery_task_id: Mapped[str | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(default="PENDING")  # PENDING/STARTED/COMPLETED/FAILED
    started_at: Mapped[dt.datetime | None] = mapped_column(default=None)
    completed_at: Mapped[dt.datetime | None] = mapped_column(default=None)

    dataset: Mapped["Dataset"] = relationship(back_populates="analysis_tasks")
    results: Mapped[list["AnalysisResult"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("analysis_tasks.id", ondelete="CASCADE"))
    metric_name: Mapped[str]
    metric_value: Mapped[float | None] = mapped_column(default=None)
    chart_data: Mapped[dict[str, Any] | None] = mapped_column(type_=JSONB, default=None)

    task: Mapped["AnalysisTask"] = relationship(back_populates="results")

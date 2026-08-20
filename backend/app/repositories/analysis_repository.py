import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.analysis import AnalysisResult, AnalysisTask


class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, dataset_id: int, task_type: str) -> AnalysisTask:
        task = AnalysisTask(
            dataset_id=dataset_id,
            task_type=task_type,
            status="PENDING",
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_task_status(
        self, task_id: int, status: str, celery_task_id: str | None = None
    ) -> AnalysisTask | None:
        task = self.get_task(task_id)
        if not task:
            return None

        task.status = status
        if celery_task_id:
            task.celery_task_id = celery_task_id
            
        if status == "STARTED":
            task.started_at = dt.datetime.now(dt.timezone.utc)
        elif status in ["COMPLETED", "FAILED"]:
            task.completed_at = dt.datetime.now(dt.timezone.utc)

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: int) -> AnalysisTask | None:
        stmt = (
            select(AnalysisTask)
            .options(selectinload(AnalysisTask.results))
            .where(AnalysisTask.id == task_id)
        )
        return self.db.scalar(stmt)

    def list_tasks(self, dataset_id: int | None = None) -> list[AnalysisTask]:
        stmt = select(AnalysisTask).order_by(AnalysisTask.id.desc())
        if dataset_id is not None:
            stmt = stmt.where(AnalysisTask.dataset_id == dataset_id)
            
        return list(self.db.scalars(stmt))

    def save_analysis_results(self, task_id: int, results_data: list[dict]) -> None:
        """
        results_data is a list of dictionaries, for example:
        [
            {"metric_name": "mean_sales", "metric_value": 150.5},
            {"metric_name": "correlation_matrix", "chart_data": {...}}
        ]
        """
        results = []
        for data in results_data:
            result = AnalysisResult(
                task_id=task_id,
                metric_name=data.get("metric_name"),
                metric_value=data.get("metric_value"),
                chart_data=data.get("chart_data"),
            )
            results.append(result)
            
        self.db.add_all(results)
        self.db.commit()

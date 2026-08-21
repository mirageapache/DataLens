import datetime as dt
from sqlalchemy import select, func, extract
from sqlalchemy.orm import Session, selectinload, aliased

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

    def list_tasks(self, page: int = 1, page_size: int = 20, dataset_id: int | None = None) -> tuple[list[AnalysisTask], int]:
        """使用 ROW_NUMBER() 實作分頁查詢"""
        base_query = select(AnalysisTask)
        if dataset_id is not None:
            base_query = base_query.where(AnalysisTask.dataset_id == dataset_id)
            
        # 建立一個包含 row_number 的子查詢
        subq = base_query.add_columns(
            func.row_number().over(order_by=AnalysisTask.id.desc()).label("rn")
        ).subquery()
        
        # 將子查詢轉回 ORM 物件，以便正確查詢與返回
        aliased_task = aliased(AnalysisTask, subq)
        
        stmt = (
            select(aliased_task)
            .where(subq.c.rn > (page - 1) * page_size)
            .where(subq.c.rn <= page * page_size)
            .order_by(subq.c.rn)
        )
        
        items = list(self.db.scalars(stmt))
        
        # 取得總筆數
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total = self.db.scalar(count_stmt) or 0
        
        return items, total

    def get_task_execution_trend(self, dataset_id: int | None = None) -> list[dict]:
        """使用 LAG() 取得任務執行時間的趨勢 (與同類型的上一筆任務比較)"""
        # 找出已完成且有開始與結束時間的任務
        base_query = (
            select(
                AnalysisTask.id,
                AnalysisTask.task_type,
                extract('epoch', AnalysisTask.completed_at - AnalysisTask.started_at).label("exec_time_sec")
            )
            .where(AnalysisTask.status == "COMPLETED")
            .where(AnalysisTask.started_at.is_not(None))
            .where(AnalysisTask.completed_at.is_not(None))
        )
        
        if dataset_id is not None:
            base_query = base_query.where(AnalysisTask.dataset_id == dataset_id)
            
        subq = base_query.subquery()
        
        # 透過 LAG 函數，依照 task_type 分組並以 id 排序，找出上一筆的執行時間
        stmt = select(
            subq.c.id.label("task_id"),
            subq.c.task_type,
            (subq.c.exec_time_sec * 1000).label("execution_time_ms"),
            (func.lag(subq.c.exec_time_sec * 1000)
             .over(partition_by=subq.c.task_type, order_by=subq.c.id)).label("prev_execution_time_ms")
        )
        
        rows = self.db.execute(stmt).all()
        
        results = []
        for r in rows:
            exec_time = float(r.execution_time_ms) if r.execution_time_ms is not None else 0.0
            prev_time = float(r.prev_execution_time_ms) if r.prev_execution_time_ms is not None else None
            time_diff = exec_time - prev_time if prev_time is not None else None
            
            results.append({
                "task_id": r.task_id,
                "task_type": r.task_type,
                "execution_time_ms": exec_time,
                "prev_execution_time_ms": prev_time,
                "time_diff_ms": time_diff
            })
            
        return results

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

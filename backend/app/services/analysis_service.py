from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import pandas as pd

from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.analysis import AnalysisRunRequest
from app.models.analysis import AnalysisTask
from app.services.statistical_analyzer import PandasAnalyzer


class AnalysisService:
    def __init__(
        self,
        analysis_repo: AnalysisRepository,
        dataset_repo: DatasetRepository,
    ):
        self.analysis_repo = analysis_repo
        self.dataset_repo = dataset_repo
        self.analyzer = PandasAnalyzer()

    def run_analysis(self, db: Session, req: AnalysisRunRequest) -> AnalysisTask:
        """
        觸發資料分析任務。
        此方法會先檢查資料集是否存在，接著在資料庫建立一個狀態為 PENDING 的任務，
        並將實際的分析工作派發給 Celery 背景 worker 處理。
        """
        # 1. 檢查資料集是否存在
        dataset = self.dataset_repo.get(req.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到指定的資料集 (ID: {req.dataset_id})"
            )

        # 2. 在資料庫建立一筆分析任務記錄
        task = self.analysis_repo.create_task(req.dataset_id, req.task_type)

        try:
            # 3. 派發任務給 Celery
            from app.tasks.analysis_tasks import run_analysis_task
            
            # 將 Pydantic model 轉換為字典格式，相容 v1 與 v2 的寫法
            req_dict = req.model_dump() if hasattr(req, "model_dump") else req.dict()
            
            # 非同步執行
            celery_task = run_analysis_task.delay(task.id, req_dict)
            
            # 4. 更新該任務對應的 Celery Task ID
            task.celery_task_id = celery_task.id
            db.commit()

        except Exception as e:
            # 發生例外時，將任務標記為失敗
            self.analysis_repo.update_task_status(task.id, "FAILED")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"派發分析任務失敗: {str(e)}"
            )

        # 回傳已建立的任務資訊 (狀態為 PENDING)
        return task

    def get_task(self, task_id: int) -> AnalysisTask:
        task = self.analysis_repo.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis task {task_id} not found."
            )
        return task

    def list_tasks(self, page: int = 1, page_size: int = 20, dataset_id: int | None = None) -> tuple[list[AnalysisTask], int]:
        return self.analysis_repo.list_tasks(page, page_size, dataset_id)

    def get_task_trend(self, dataset_id: int | None = None) -> list[dict]:
        return self.analysis_repo.get_task_execution_trend(dataset_id)

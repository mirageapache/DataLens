from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.analysis import (
    AnalysisRunRequest,
    AnalysisTaskRead,
    AnalysisTaskDetailRead,
    AnalysisResultRead,
)
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])


def get_analysis_service(db: Session = Depends(get_db)) -> AnalysisService:
    analysis_repo = AnalysisRepository(db)
    dataset_repo = DatasetRepository(db)
    return AnalysisService(analysis_repo, dataset_repo)


@router.post("/run", response_model=AnalysisTaskRead)
def run_analysis(
    req: AnalysisRunRequest,
    db: Session = Depends(get_db),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    觸發分析任務 (Phase 2-1: 同步執行)
    """
    task = service.run_analysis(db, req)
    return task


@router.get("/tasks", response_model=list[AnalysisTaskRead])
def list_tasks(
    dataset_id: int | None = Query(None, description="依據 dataset_id 篩選"),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    列出分析任務歷史
    """
    tasks = service.list_tasks(dataset_id=dataset_id)
    return tasks


@router.get("/tasks/{task_id}", response_model=AnalysisTaskRead)
def get_task(
    task_id: int,
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    查詢分析任務狀態
    """
    task = service.get_task(task_id)
    return task


@router.get("/tasks/{task_id}/results", response_model=list[AnalysisResultRead])
def get_task_results(
    task_id: int,
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    取得分析結果 (不包含 chart_data，以減輕 payload)
    """
    task = service.get_task(task_id)
    # We can create a schema to exclude chart_data if needed, but for now we just return them
    return task.results


@router.get("/tasks/{task_id}/charts")
def get_task_charts(
    task_id: int,
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    取得圖表所需 JSON 資料
    """
    task = service.get_task(task_id)
    # Return just the chart_data
    charts = {}
    for result in task.results:
        if result.chart_data:
            charts[result.metric_name] = result.chart_data
    return charts

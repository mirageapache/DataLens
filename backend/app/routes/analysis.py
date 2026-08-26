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
    AnalysisResultSummaryRead,
    AnalysisTaskListResponse,
    TaskExecutionTrendRead,
    ChartDataResponse,
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
    觸發分析任務 (Phase 2-2: 改為非同步執行)
    """
    task = service.run_analysis(db, req)
    return task


@router.get("/tasks", response_model=AnalysisTaskListResponse)
def list_tasks(
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁筆數"),
    dataset_id: int | None = Query(None, description="依據 dataset_id 篩選"),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    列出分析任務歷史 (包含 ROW_NUMBER() 分頁實作)
    """
    tasks, total = service.list_tasks(page=page, page_size=page_size, dataset_id=dataset_id)
    return AnalysisTaskListResponse(
        items=tasks,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/tasks/trend", response_model=list[TaskExecutionTrendRead])
def get_task_trend(
    dataset_id: int | None = Query(None, description="依據 dataset_id 篩選"),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    取得任務執行時間趨勢 (包含 LAG() 函數實作)
    """
    return service.get_task_trend(dataset_id=dataset_id)


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


@router.get("/tasks/{task_id}/results", response_model=list[AnalysisResultSummaryRead])
def get_task_results(
    task_id: int,
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    取得分析結果 (不包含 chart_data，以減輕 payload)
    """
    task = service.get_task(task_id)
    return task.results


@router.get("/tasks/{task_id}/charts", response_model=dict[str, ChartDataResponse])
def get_task_charts(
    task_id: int,
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    取得圖表所需 JSON 資料（含推薦圖表類型）
    """
    task = service.get_task(task_id)
    charts = {}
    for result in task.results:
        if result.chart_data:
            recommended = service.get_recommended_charts_for_metric(result.metric_name, task.task_type)
            charts[result.metric_name] = ChartDataResponse(
                recommended_charts=recommended,
                chart_data=result.chart_data
            )
    return charts

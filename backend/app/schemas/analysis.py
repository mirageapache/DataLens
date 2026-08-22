import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalysisRunRequest(BaseModel):
    """分析請求模型"""

    dataset_id: int
    task_type: Literal["descriptive", "correlation", "group_by", "time_series"]
    
    # 針對特定分析的額外參數
    target_columns: list[str] | None = Field(
        default=None, description="要進行分析的特定欄位，若未提供則分析所有支援的欄位"
    )
    
    # 時間序列特有參數 (Option 2: 透過前端傳入參數去調整資料呈現的維度)
    freq: Literal["D", "W", "M", "Y"] | None = Field(
        default=None, description="時間序列聚合頻率：D(日), W(週), M(月), Y(年)"
    )
    time_column: str | None = Field(
        default=None, description="時間序列的時間欄位，若未提供則由後端自動推測"
    )
    
    # 分組特有參數
    group_by_column: str | None = Field(default=None, description="分組依據的欄位")
    agg_funcs: list[str] | None = Field(
        default=None, description="聚合函式列表，如 ['sum', 'mean', 'count']"
    )


class AnalysisResultSummaryRead(BaseModel):
    """單筆分析結果的回傳模型 (不包含 chart_data 以減輕 Payload)"""
    id: int
    task_id: int
    metric_name: str
    metric_value: float | None = None

    model_config = {"from_attributes": True}


class AnalysisResultRead(AnalysisResultSummaryRead):
    """單筆分析結果的完整回傳模型 (包含 chart_data)"""
    chart_data: dict[str, Any] | None = None


class AnalysisTaskRead(BaseModel):
    """分析任務狀態與基本資訊的回傳模型"""

    id: int
    dataset_id: int
    task_type: str
    status: str
    started_at: dt.datetime | None = None
    completed_at: dt.datetime | None = None

    model_config = {"from_attributes": True}


class AnalysisTaskDetailRead(AnalysisTaskRead):
    """包含分析結果的完整任務資訊"""

    results: list[AnalysisResultRead] = Field(default_factory=list)


class TaskExecutionTrendRead(BaseModel):
    """任務執行時間趨勢模型"""
    task_id: int
    task_type: str
    execution_time_ms: float
    prev_execution_time_ms: float | None = None
    time_diff_ms: float | None = None


class AnalysisTaskListResponse(BaseModel):
    """分析任務列表的分頁回應模型"""
    items: list[AnalysisTaskRead]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)

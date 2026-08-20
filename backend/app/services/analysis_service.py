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
        # 1. Check if dataset exists
        dataset = self.dataset_repo.get(req.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {req.dataset_id} not found."
            )

        # 2. Create Task
        task = self.analysis_repo.create_task(req.dataset_id, req.task_type)

        try:
            # 3. Read Data (For Phase 2-1 this is synchronous)
            self.analysis_repo.update_task_status(task.id, "STARTED")
            
            # Use pandas to read the file
            if dataset.file_path.endswith('.csv'):
                df = pd.read_csv(dataset.file_path)
            elif dataset.file_path.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(dataset.file_path)
            else:
                raise ValueError("Unsupported file format for analysis.")

            # 4. Run Analysis
            results_data = []
            
            if req.task_type == "descriptive":
                results_data = self.analyzer.descriptive_stats(df, req.target_columns)
            elif req.task_type == "correlation":
                results_data = self.analyzer.correlation_matrix(df, req.target_columns)
            elif req.task_type == "group_by":
                if not req.group_by_column:
                    raise ValueError("group_by_column is required for group_by analysis")
                agg_funcs = req.agg_funcs or ["mean", "sum", "count"]
                results_data = self.analyzer.group_by_aggregation(df, req.group_by_column, agg_funcs)
            elif req.task_type == "time_series":
                freq = req.freq or "M"
                results_data = self.analyzer.time_series_trend(df, freq)
            else:
                raise ValueError(f"Unknown task type: {req.task_type}")

            # 5. Save Results
            self.analysis_repo.save_analysis_results(task.id, results_data)
            
            # 6. Update Task Status
            self.analysis_repo.update_task_status(task.id, "COMPLETED")

        except Exception as e:
            self.analysis_repo.update_task_status(task.id, "FAILED")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analysis failed: {str(e)}"
            )

        return self.analysis_repo.get_task(task.id)

    def get_task(self, task_id: int) -> AnalysisTask:
        task = self.analysis_repo.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis task {task_id} not found."
            )
        return task

    def list_tasks(self, dataset_id: int | None = None) -> list[AnalysisTask]:
        return self.analysis_repo.list_tasks(dataset_id)

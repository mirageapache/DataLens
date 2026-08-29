import logging
from pathlib import Path

import pandas as pd
from celery.exceptions import Ignore

from app.core.celery_app import celery_app
from app.core.config import UPLOAD_ROOT
from app.core.db import SessionLocal
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.dataset_repository import DatasetRepository
from app.services.statistical_analyzer import PandasAnalyzer

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.analysis_tasks.run_analysis_task")
def run_analysis_task(self, task_id: int, req_dict: dict):
    logger.info(f"開始執行分析任務 {task_id}")
    # 在背景任務中建立新的資料庫連線
    db = SessionLocal()
    try:
        analysis_repo = AnalysisRepository(db)
        dataset_repo = DatasetRepository(db)
        analyzer = PandasAnalyzer()

        task = analysis_repo.get_task(task_id)
        if not task:
            logger.error(f"在資料庫中找不到任務 {task_id}。")
            return

        dataset_id = req_dict.get("dataset_id")
        dataset = dataset_repo.get(dataset_id)
        if not dataset:
            logger.error(f"找不到資料集 {dataset_id}。")
            analysis_repo.update_task_status(task.id, "FAILED")
            return

        # 更新任務狀態為已開始
        analysis_repo.update_task_status(task.id, "STARTED")
        analysis_repo.update_task_progress(task.id, 10)

        # 1. 讀取資料，並驗證路徑安全性
        full_file_path = (UPLOAD_ROOT / dataset.file_path).resolve()
        if not full_file_path.is_relative_to(UPLOAD_ROOT.resolve()):
            logger.error("任務 %d 偵測到可疑的 Path Traversal：file_path=%s", task_id, dataset.file_path)
            analysis_repo.update_task_status(task.id, "FAILED")
            raise Ignore()

        if dataset.file_path.endswith('.csv'):
            df = pd.read_csv(full_file_path)
        elif dataset.file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(full_file_path)
        else:
            raise ValueError("不支援的分析檔案格式。")
            
        analysis_repo.update_task_progress(task.id, 30)

        # 2. 執行分析
        results_data = []
        task_type = req_dict.get("task_type")
        target_columns = req_dict.get("target_columns")

        if task_type == "descriptive":
            results_data = analyzer.descriptive_stats(df, target_columns)
        elif task_type == "descriptive_with_correlation":
            # 明確包含相關性分析的組合任務類型，供前端 Dashboard 使用
            results_data = analyzer.descriptive_with_correlation(df, target_columns)
        elif task_type == "correlation":
            results_data = analyzer.correlation_matrix(df, target_columns)
        elif task_type == "group_by":
            group_by_column = req_dict.get("group_by_column")
            if not group_by_column:
                raise ValueError("group_by 分析必須提供 group_by_column")
            agg_funcs = req_dict.get("agg_funcs") or ["mean", "sum", "count"]
            results_data = analyzer.group_by_aggregation(df, group_by_column, agg_funcs)
        elif task_type == "time_series":
            freq = req_dict.get("freq") or "M"
            time_column = req_dict.get("time_column")
            # If user provides agg_funcs for time_series, we can use the first one, else "sum"
            agg_funcs = req_dict.get("agg_funcs")
            agg_func = agg_funcs[0] if agg_funcs else "sum"
            results_data = analyzer.time_series_trend(df, freq=freq, time_column=time_column, agg_func=agg_func)
        elif task_type == "distribution":
            results_data = analyzer.distribution_and_outliers(df, target_columns)
        elif task_type == "cross_tabulation":
            index_col = req_dict.get("cross_tab_index_column")
            cols_col = req_dict.get("cross_tab_columns_column")
            val_col = req_dict.get("cross_tab_value_column")
            agg_func = req_dict.get("cross_tab_agg_func") or "count"
            if not index_col or not cols_col:
                raise ValueError("cross_tabulation 必須提供 cross_tab_index_column 與 cross_tab_columns_column")
            results_data = analyzer.cross_tabulation(df, index_column=index_col, columns_column=cols_col, value_column=val_col, agg_func=agg_func)
        else:
            raise ValueError(f"未知的任務類型: {task_type}")

        analysis_repo.update_task_progress(task.id, 80)

        # 3. 儲存分析結果
        analysis_repo.save_analysis_results(task.id, results_data)
        
        # 4. 更新任務狀態為已完成
        analysis_repo.update_task_progress(task.id, 100)
        analysis_repo.update_task_status(task.id, "COMPLETED")
        logger.info(f"分析任務 {task_id} 成功完成。")

    except Exception as e:
        logger.error(f"分析任務 {task_id} 失敗: {e}")
        try:
            # 發生例外時嘗試將任務標記為失敗
            analysis_repo = AnalysisRepository(db)
            analysis_repo.update_task_status(task_id, "FAILED")
        except Exception as inner_e:
            logger.error(f"更新任務 {task_id} 狀態為 FAILED 時發生錯誤: {inner_e}")
        # 拋出 Ignore 例外，讓 Celery 知道此任務失敗且已處理，不要重試
        raise Ignore()
    finally:
        # 確保關閉資料庫連線
        db.close()

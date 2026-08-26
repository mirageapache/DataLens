import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.services.analysis_service import AnalysisService

@pytest.fixture
def mock_analysis_repo():
    return Mock()

@pytest.fixture
def mock_dataset_repo():
    return Mock()

@pytest.fixture
def analysis_service(mock_analysis_repo, mock_dataset_repo):
    return AnalysisService(analysis_repo=mock_analysis_repo, dataset_repo=mock_dataset_repo)

def test_get_recommended_charts_for_metric(analysis_service):
    """測試根據指標名稱推薦適合的圖表類型"""
    
    # 測試 boxplot
    assert analysis_service.get_recommended_charts_for_metric("distribution_boxplot_col1", "distribution") == ["boxplot"]
    
    # 測試 correlation
    assert analysis_service.get_recommended_charts_for_metric("pearson_correlation_matrix", "correlation") == ["heatmap"]
    
    # 測試 descriptive stats
    assert analysis_service.get_recommended_charts_for_metric("descriptive_stats_sales", "descriptive") == ["histogram", "bar"]
    
    # 測試 group by
    assert analysis_service.get_recommended_charts_for_metric("group_by_category", "group_by") == ["bar", "pie", "donut"]
    
    # 測試 time series
    assert analysis_service.get_recommended_charts_for_metric("time_series_trend_M", "time_series") == ["line", "area", "dual_axis"]
    
    # 測試 cross tab
    assert analysis_service.get_recommended_charts_for_metric("cross_tab_category_region", "cross_tab") == ["stacked_bar", "heatmap"]
    
    # 測試 fallback default
    assert analysis_service.get_recommended_charts_for_metric("unknown_metric", "unknown_task") == ["bar"]

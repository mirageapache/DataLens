import pandas as pd
import pytest
from fastapi import HTTPException

from app.services.statistical_analyzer import PandasAnalyzer


@pytest.fixture
def sample_df():
    data = {
        "id": [1, 2, 3, 4, 5],
        "category": ["A", "B", "A", "B", "A"],
        "value1": [10, 20, 30, 40, 50],
        "value2": [5.5, 6.6, 7.7, 8.8, 9.9],
        "date": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"])
    }
    return pd.DataFrame(data)


def test_check_limit(sample_df):
    analyzer = PandasAnalyzer()
    analyzer._check_limit(sample_df)  # Should not raise
    
    # Test exceeding limit
    large_df = pd.DataFrame({"col": range(PandasAnalyzer.MAX_ROWS_LIMIT + 1)})
    with pytest.raises(HTTPException) as excinfo:
        analyzer._check_limit(large_df)
    assert excinfo.value.status_code == 400


def test_descriptive_stats(sample_df):
    analyzer = PandasAnalyzer()
    results = analyzer.descriptive_stats(sample_df)
    
    # Should calculate stats for numeric columns (id, value1, value2)
    assert len(results) == 3
    metric_names = [r["metric_name"] for r in results]
    assert "descriptive_stats_value1" in metric_names
    
    # Check value1 mean (30.0)
    v1_stats = next(r["chart_data"] for r in results if r["metric_name"] == "descriptive_stats_value1")
    assert v1_stats["mean"] == 30.0
    assert v1_stats["count"] == 5.0


def test_correlation_matrix(sample_df):
    analyzer = PandasAnalyzer()
    results = analyzer.correlation_matrix(sample_df, target_columns=["value1", "value2"])
    
    assert len(results) == 1
    assert results[0]["metric_name"] == "pearson_correlation_matrix"
    chart_data = results[0]["chart_data"]
    
    assert chart_data["columns"] == ["value1", "value2"]
    # Correlation between perfectly correlated lines is 1.0
    assert chart_data["values"][0][1] == pytest.approx(1.0)


def test_group_by_aggregation(sample_df):
    analyzer = PandasAnalyzer()
    results = analyzer.group_by_aggregation(sample_df, "category", ["sum", "mean"])
    
    assert len(results) == 1
    assert results[0]["metric_name"] == "group_by_category"
    chart_data = results[0]["chart_data"]
    
    assert chart_data["categories"] == ["A", "B"]
    
    # Check A's value1 sum (10 + 30 + 50 = 90)
    assert chart_data["series"]["sum_value1"] == [90.0, 60.0]


def test_time_series_trend(sample_df):
    analyzer = PandasAnalyzer()
    results = analyzer.time_series_trend(sample_df, freq="D")
    
    assert len(results) == 1
    assert results[0]["metric_name"] == "time_series_trend_D"
    chart_data = results[0]["chart_data"]
    
    assert len(chart_data["time_labels"]) == 5
    assert chart_data["time_labels"][0] == "2023-01-01"
    assert chart_data["series"]["value1"] == [10.0, 20.0, 30.0, 40.0, 50.0]

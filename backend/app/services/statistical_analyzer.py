from abc import ABC, abstractmethod
from typing import Any

import pandas as pd
from fastapi import HTTPException, status


class BaseAnalyzer(ABC):
    @abstractmethod
    def descriptive_stats(self, df: pd.DataFrame, target_columns: list[str] | None = None) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def correlation_matrix(self, df: pd.DataFrame, target_columns: list[str] | None = None) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def group_by_aggregation(self, df: pd.DataFrame, group_by_column: str, agg_funcs: list[str]) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def time_series_trend(self, df: pd.DataFrame, freq: str = "M") -> list[dict[str, Any]]:
        pass


class PandasAnalyzer(BaseAnalyzer):
    MAX_ROWS_LIMIT = 500000

    def _check_limit(self, df: pd.DataFrame) -> None:
        if len(df) > self.MAX_ROWS_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"資料量過大 ({len(df)} 筆)，目前同步分析僅支援 {self.MAX_ROWS_LIMIT} 筆以內。"
            )

    def descriptive_stats(self, df: pd.DataFrame, target_columns: list[str] | None = None) -> list[dict[str, Any]]:
        self._check_limit(df)
        
        # Select numeric columns
        if target_columns:
            df = df[target_columns]
            
        numeric_df = df.select_dtypes(include="number")
        if numeric_df.empty:
            return []

        # Calculate stats
        stats = numeric_df.describe().T
        stats["skewness"] = numeric_df.skew()
        stats["kurtosis"] = numeric_df.kurt()
        
        results = []
        for col in stats.index:
            col_stats = stats.loc[col].to_dict()
            results.append({
                "metric_name": f"descriptive_stats_{col}",
                "chart_data": col_stats
            })
            
        return results

    def correlation_matrix(self, df: pd.DataFrame, target_columns: list[str] | None = None) -> list[dict[str, Any]]:
        self._check_limit(df)
        
        if target_columns:
            df = df[target_columns]
            
        numeric_df = df.select_dtypes(include="number")
        if numeric_df.empty:
            return []

        corr_matrix = numeric_df.corr(method="pearson")
        
        # Format for heatmap: x (columns), y (columns), and values
        chart_data = {
            "columns": list(corr_matrix.columns),
            "values": corr_matrix.values.tolist()
        }
        
        return [{
            "metric_name": "pearson_correlation_matrix",
            "chart_data": chart_data
        }]

    def group_by_aggregation(self, df: pd.DataFrame, group_by_column: str, agg_funcs: list[str]) -> list[dict[str, Any]]:
        self._check_limit(df)
        
        if group_by_column not in df.columns:
            raise ValueError(f"Column '{group_by_column}' not found in dataset.")
            
        # Support basic numeric agg functions
        valid_funcs = [f for f in agg_funcs if f in ["sum", "mean", "count", "max", "min"]]
        if not valid_funcs:
            valid_funcs = ["count"]

        grouped = df.groupby(group_by_column).agg(valid_funcs)
        
        # Format the result so it can be easily plotted as a bar/line chart
        chart_data = {
            "categories": [str(idx) for idx in grouped.index],
            "series": {}
        }
        
        # Iterate over multi-index columns resulting from .agg()
        for col_name, func_name in grouped.columns:
            series_name = f"{func_name}_{col_name}"
            # Need to replace NaNs/Inf with None to be valid JSON
            values = grouped[(col_name, func_name)].fillna(0).tolist()
            chart_data["series"][series_name] = values

        return [{
            "metric_name": f"group_by_{group_by_column}",
            "chart_data": chart_data
        }]

    def time_series_trend(self, df: pd.DataFrame, freq: str = "M", time_column: str | None = None) -> list[dict[str, Any]]:
        self._check_limit(df)
        
        if time_column and time_column in df.columns:
            df[time_column] = pd.to_datetime(df[time_column], errors="coerce")
            time_col = time_column
        else:
            datetime_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns
            
            # If no explicit datetime column, try to infer it by parsing strings
            if datetime_cols.empty:
                object_cols = df.select_dtypes(include=["object"]).columns
                for col in object_cols:
                    try:
                        df[col] = pd.to_datetime(df[col])
                        datetime_cols = [col]
                        break
                    except (ValueError, TypeError):
                        continue
            
            if not datetime_cols or len(datetime_cols) == 0:
                return []
                
            time_col = datetime_cols[0]
            
        numeric_df = df.select_dtypes(include="number")
        
        if numeric_df.empty:
            return []
            
        # Group by the specified frequency ('D', 'W', 'M', 'Y')
        temp_df = pd.DataFrame()
        temp_df[time_col] = df[time_col]
        for col in numeric_df.columns:
            temp_df[col] = numeric_df[col]
            
        grouped = temp_df.groupby(pd.Grouper(key=time_col, freq=freq)).sum(numeric_only=True)
        
        chart_data = {
            "time_labels": [idx.strftime("%Y-%m-%d") for idx in grouped.index],
            "series": {}
        }
        
        for col in grouped.columns:
            chart_data["series"][col] = grouped[col].fillna(0).tolist()
            
        return [{
            "metric_name": f"time_series_trend_{freq}",
            "chart_data": chart_data
        }]

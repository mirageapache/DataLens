import datetime as dt

import pytest
from pydantic import ValidationError

from app.schemas.dataset import (
    DatasetColumnRead,
    DatasetListResponse,
    DatasetRead,
    DatasetUpdate,
)


def test_dataset_column_read_schema():
    """測試 DatasetColumnRead 模型欄位定義與預設行為。"""
    col_data = {
        "id": 1,
        "column_name": "age",
        "data_type": "numeric",
        "null_count": 5,
        "unique_count": 40,
    }
    col = DatasetColumnRead.model_validate(col_data)
    assert col.id == 1
    assert col.column_name == "age"
    assert col.data_type == "numeric"
    assert col.null_count == 5
    assert col.unique_count == 40


def test_dataset_read_schema():
    """測試 DatasetRead 模型及其嵌套欄位 columns。"""
    now = dt.datetime.now(dt.timezone.utc)
    dataset_data = {
        "id": 10,
        "filename": "data.csv",
        "file_path": "uploads/abc.csv",
        "row_count": 100,
        "column_count": 1,
        "status": "ready",
        "created_at": now,
        "columns": [
            {
                "id": 1,
                "column_name": "score",
                "data_type": "numeric",
                "null_count": 0,
                "unique_count": 20,
            }
        ],
    }
    dataset = DatasetRead.model_validate(dataset_data)
    assert dataset.id == 10
    assert dataset.filename == "data.csv"
    assert len(dataset.columns) == 1
    assert dataset.columns[0].column_name == "score"


def test_dataset_list_response_valid():
    """測試 DatasetListResponse 在合法參數下的建構。"""
    response = DatasetListResponse(
        items=[],
        total=0,
        page=1,
        page_size=50,
    )
    assert response.page == 1
    assert response.page_size == 50
    assert response.total == 0
    assert response.items == []


def test_dataset_list_response_invalid_page_constraints():
    """測試 DatasetListResponse 的分頁邊界驗證 (page >= 1, 1 <= page_size <= 100)。"""
    # page < 1
    with pytest.raises(ValidationError):
        DatasetListResponse(items=[], total=0, page=0, page_size=20)

    # page_size < 1
    with pytest.raises(ValidationError):
        DatasetListResponse(items=[], total=0, page=1, page_size=0)

    # page_size > 100
    with pytest.raises(ValidationError):
        DatasetListResponse(items=[], total=0, page=1, page_size=101)


def test_dataset_update_schema_partial():
    """測試 DatasetUpdate 支援空值及部分欄位更新。"""
    # 空更新
    empty_update = DatasetUpdate()
    assert empty_update.status is None
    assert empty_update.filename is None

    # 只更新 status
    status_update = DatasetUpdate(status="processing")
    assert status_update.status == "processing"
    assert status_update.filename is None

    # 只更新 filename
    name_update = DatasetUpdate(filename="new_name.csv")
    assert name_update.filename == "new_name.csv"
    assert name_update.status is None

from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest
from fastapi import HTTPException, UploadFile

from app.schemas.dataset import DatasetUpdate
from app.services.dataset_service import DatasetService


def test_upload_csv_success(
    dataset_service: DatasetService,
    make_csv_upload_file,
    temp_upload_dir: Path,
):
    """測試成功上傳並解析 CSV 檔案，驗證回傳資料與欄位統計。"""
    csv_content = (
        "id,name,salary,hire_date\n"
        "1,Alice,50000.0,2023-01-15\n"
        "2,Bob,62000.5,2022-06-01\n"
        "3,Charlie,,2021-09-10\n"
    )
    upload_file = make_csv_upload_file(csv_content, filename="employees.csv")

    result = dataset_service.upload_dataset(upload_file)

    assert result.id is not None
    assert result.filename == "employees.csv"
    assert result.status == "ready"
    assert result.row_count == 3
    assert result.column_count == 4
    assert len(result.columns) == 4

    col_map = {col.column_name: col for col in result.columns}

    # 驗證 id 欄位 (numeric)
    assert col_map["id"].data_type == "numeric"
    assert col_map["id"].null_count == 0
    assert col_map["id"].unique_count == 3

    # 驗證 name 欄位 (categorical)
    assert col_map["name"].data_type == "categorical"
    assert col_map["name"].null_count == 0
    assert col_map["name"].unique_count == 3

    # 驗證 salary 欄位 (numeric, 含 1 個缺值)
    assert col_map["salary"].data_type == "numeric"
    assert col_map["salary"].null_count == 1
    assert col_map["salary"].unique_count == 2

    # 驗證檔案是否確實寫入暫存目錄
    assert (temp_upload_dir / result.file_path).exists()


def test_upload_excel_xlsx_success(
    dataset_service: DatasetService,
    make_excel_upload_file,
    temp_upload_dir: Path,
):
    """測試成功上傳並解析 XLSX 格式的 Excel 檔案。"""
    df = pd.DataFrame({
        "category": ["Electronics", "Clothing", "Home"],
        "price": [299.99, 49.50, 15.00],
        "in_stock": [True, False, True],
    })
    upload_file = make_excel_upload_file(df, filename="products.xlsx")

    result = dataset_service.upload_dataset(upload_file)

    assert result.filename == "products.xlsx"
    assert result.row_count == 3
    assert result.column_count == 3
    assert result.status == "ready"
    assert len(result.columns) == 3

    assert (temp_upload_dir / result.file_path).exists()


def test_upload_excel_xls_extension_accepted(
    dataset_service: DatasetService,
    make_excel_upload_file,
    temp_upload_dir: Path,
):
    """測試 .xls 副檔名被接受並走 pd.read_excel 路徑。

    注意：fixture 產生的實際內容為 xlsx 格式（openpyxl），
    尚未涵蓋傳統 Excel 97-2003 (.xls) 二進位格式的解析。
    """
    df = pd.DataFrame({"score": [85, 90, 78]})
    upload_file = make_excel_upload_file(df, filename="scores.xls")

    result = dataset_service.upload_dataset(upload_file)

    assert result.filename == "scores.xls"
    assert result.row_count == 3
    assert result.column_count == 1


def test_upload_missing_filename(dataset_service: DatasetService):
    """測試未提供檔名時拋出 400 Bad Request。"""
    upload_file = UploadFile(file=BytesIO(b"a,b\n1,2"), filename="")

    with pytest.raises(HTTPException) as exc_info:
        dataset_service.upload_dataset(upload_file)

    assert exc_info.value.status_code == 400
    assert "File name is required" in exc_info.value.detail


def test_upload_unsupported_file_extension(dataset_service: DatasetService):
    """測試上傳不支援的檔案格式（如 .txt, .json）時拋出 400。"""
    upload_file = UploadFile(file=BytesIO(b"some content"), filename="data.txt")

    with pytest.raises(HTTPException) as exc_info:
        dataset_service.upload_dataset(upload_file)

    assert exc_info.value.status_code == 400
    assert "Only CSV/XLSX/XLS files are supported" in exc_info.value.detail


def test_upload_corrupted_file_cleans_up(
    dataset_service: DatasetService,
    temp_upload_dir: Path,
):
    """測試損毀的檔案在解析失敗時拋出 400，並清理暫存的實體檔案。"""
    corrupted_bytes = b"\x00\x01\x02InvalidExcelOrCSVData\xff\xfe"
    upload_file = UploadFile(file=BytesIO(corrupted_bytes), filename="broken.xlsx")

    with pytest.raises(HTTPException) as exc_info:
        dataset_service.upload_dataset(upload_file)

    assert exc_info.value.status_code == 400
    assert "Unable to parse file" in exc_info.value.detail
    # 驗證沒有殘留的孤兒檔案
    assert len(list(temp_upload_dir.glob("*.xlsx"))) == 0


def test_column_type_detection(
    dataset_service: DatasetService,
    make_csv_upload_file,
    make_excel_upload_file,
):
    """測試數值、日期時間與類別型別的自動偵測機制。"""
    # 1. 測試 CSV (numeric, categorical)
    csv_content = (
        "int_col,float_col,str_col\n"
        "10,1.5,apple\n"
        "20,2.5,banana\n"
        "30,3.5,cherry\n"
    )
    upload_csv = make_csv_upload_file(csv_content, filename="types_test.csv")
    result_csv = dataset_service.upload_dataset(upload_csv)
    col_map_csv = {col.column_name: col.data_type for col in result_csv.columns}

    assert col_map_csv["int_col"] == "numeric"
    assert col_map_csv["float_col"] == "numeric"
    assert col_map_csv["str_col"] == "categorical"

    # 2. 測試 Excel 包含真實 datetime 型別欄位
    df = pd.DataFrame({
        "timestamp_col": pd.to_datetime(["2026-05-01", "2026-05-02", "2026-05-03"]),
        "num_col": [100, 200, 300],
    })
    upload_excel = make_excel_upload_file(df, filename="types_test.xlsx")
    result_excel = dataset_service.upload_dataset(upload_excel)
    col_map_excel = {col.column_name: col.data_type for col in result_excel.columns}

    assert col_map_excel["timestamp_col"] == "datetime"
    assert col_map_excel["num_col"] == "numeric"


def test_null_and_unique_counts(
    dataset_service: DatasetService,
    make_csv_upload_file,
):
    """測試缺值計數與唯一值計數（排除 NaN）的精準度。"""
    csv_content = (
        "category,score\n"
        "alpha,10.0\n"
        "beta,\n"
        ",20.0\n"
        "alpha,10.0\n"
        ",\n"
    )
    upload_file = make_csv_upload_file(csv_content, filename="nulls.csv")

    result = dataset_service.upload_dataset(upload_file)
    col_map = {col.column_name: col for col in result.columns}

    # category: ['alpha', 'beta', NaN, 'alpha', NaN] -> null=2, unique=2 ('alpha', 'beta')
    assert col_map["category"].null_count == 2
    assert col_map["category"].unique_count == 2

    # score: [10.0, NaN, 20.0, 10.0, NaN] -> null=2, unique=2 (10.0, 20.0)
    assert col_map["score"].null_count == 2
    assert col_map["score"].unique_count == 2


def test_list_datasets_empty(dataset_service: DatasetService):
    """測試在尚無資料集時，列表 API 回傳空清單與 total=0。"""
    response = dataset_service.list_datasets(page=1, page_size=10)
    assert response.items == []
    assert response.total == 0
    assert response.page == 1
    assert response.page_size == 10


def test_list_datasets_pagination(
    dataset_service: DatasetService,
    make_csv_upload_file,
):
    """測試多筆資料集的分頁列出功能。"""
    for i in range(3):
        upload_file = make_csv_upload_file(f"col\n{i}", filename=f"file_{i}.csv")
        dataset_service.upload_dataset(upload_file)

    page1 = dataset_service.list_datasets(page=1, page_size=2)
    assert len(page1.items) == 2
    assert page1.total == 3
    assert page1.page == 1
    assert page1.page_size == 2

    page2 = dataset_service.list_datasets(page=2, page_size=2)
    assert len(page2.items) == 1
    assert page2.total == 3
    assert page2.page == 2


def test_get_dataset_success(
    dataset_service: DatasetService,
    make_csv_upload_file,
):
    """測試依 ID 取得單一資料集與其欄位列表。"""
    upload_file = make_csv_upload_file("x,y\n1,2", filename="points.csv")
    created = dataset_service.upload_dataset(upload_file)

    fetched = dataset_service.get_dataset(created.id)
    assert fetched.id == created.id
    assert fetched.filename == "points.csv"
    assert len(fetched.columns) == 2


def test_get_dataset_not_found(dataset_service: DatasetService):
    """測試查詢不存在的資料集 ID 時拋出 404 Not Found。"""
    with pytest.raises(HTTPException) as exc_info:
        dataset_service.get_dataset(99999)

    assert exc_info.value.status_code == 404
    assert "Dataset not found" in exc_info.value.detail


def test_update_dataset_success(
    dataset_service: DatasetService,
    make_csv_upload_file,
):
    """測試更新資料集名稱與狀態。"""
    upload_file = make_csv_upload_file("val\n100", filename="original.csv")
    created = dataset_service.upload_dataset(upload_file)

    update_payload = DatasetUpdate(filename="renamed.csv", status="processing")
    updated = dataset_service.update_dataset(created.id, update_payload)

    assert updated.id == created.id
    assert updated.filename == "renamed.csv"
    assert updated.status == "processing"


def test_update_dataset_partial(
    dataset_service: DatasetService,
    make_csv_upload_file,
):
    """測試部分欄位更新（例如只更新 status）。"""
    upload_file = make_csv_upload_file("val\n100", filename="test.csv")
    created = dataset_service.upload_dataset(upload_file)

    update_payload = DatasetUpdate(status="failed")
    updated = dataset_service.update_dataset(created.id, update_payload)

    assert updated.filename == "test.csv"  # 保持不變
    assert updated.status == "failed"


def test_update_dataset_not_found(dataset_service: DatasetService):
    """測試更新不存在的資料集 ID 時拋出 404。"""
    with pytest.raises(HTTPException) as exc_info:
        dataset_service.update_dataset(99999, DatasetUpdate(status="ready"))

    assert exc_info.value.status_code == 404
    assert "Dataset not found" in exc_info.value.detail


def test_delete_dataset_success(
    dataset_service: DatasetService,
    make_csv_upload_file,
    temp_upload_dir: Path,
):
    """測試刪除資料集：資料庫記錄移除且實體檔案一併被刪除。"""
    upload_file = make_csv_upload_file("a,b\n1,2", filename="to_delete.csv")
    created = dataset_service.upload_dataset(upload_file)

    saved_file_path = temp_upload_dir / created.file_path
    assert saved_file_path.exists()

    dataset_service.delete_dataset(created.id)

    # 驗證實體檔案已被刪除
    assert not saved_file_path.exists()

    # 驗證再次查詢拋出 404
    with pytest.raises(HTTPException) as exc_info:
        dataset_service.get_dataset(created.id)
    assert exc_info.value.status_code == 404


def test_delete_dataset_not_found(dataset_service: DatasetService):
    """測試刪除不存在的資料集 ID 時拋出 404。"""
    with pytest.raises(HTTPException) as exc_info:
        dataset_service.delete_dataset(99999)

    assert exc_info.value.status_code == 404
    assert "Dataset not found" in exc_info.value.detail


def test_upload_file_exceeds_max_size(dataset_service: DatasetService, monkeypatch):
    """測試上傳檔案大小超過上限 (50MB) 拋出 413 Payload Too Large。"""
    # 模擬超過 50MB 的資料讀取
    oversized_bytes = b"x" * (50 * 1024 * 1024 + 1)
    upload_file = UploadFile(file=BytesIO(oversized_bytes), filename="huge.csv")

    with pytest.raises(HTTPException) as exc_info:
        dataset_service.upload_dataset(upload_file)

    assert exc_info.value.status_code == 413
    assert "File too large" in exc_info.value.detail


def test_delete_dataset_handles_os_error(
    dataset_service: DatasetService,
    make_csv_upload_file,
    monkeypatch,
):
    """測試實體檔案刪除拋出 OSError 時不阻斷流程，資料庫仍正常刪除。"""
    upload_file = make_csv_upload_file("a\n1", filename="error.csv")
    created = dataset_service.upload_dataset(upload_file)

    def _mock_unlink(self, *args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "unlink", _mock_unlink)

    # 刪除不應崩潰拋出異常
    dataset_service.delete_dataset(created.id)

    # 驗證 DB 記錄已被刪除
    with pytest.raises(HTTPException) as exc_info:
        dataset_service.get_dataset(created.id)
    assert exc_info.value.status_code == 404

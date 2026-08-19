import io
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """測試健康檢查 API 端點。"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_dataset_route_success(client: TestClient):
    """測試 POST /api/v1/datasets/upload 上傳 CSV。"""
    csv_bytes = b"id,val\n1,100\n2,200\n"
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("sample.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "sample.csv"
    assert data["row_count"] == 2
    assert data["column_count"] == 2
    assert data["status"] == "ready"
    assert len(data["columns"]) == 2


def test_upload_dataset_route_invalid_extension(client: TestClient):
    """測試 POST /api/v1/datasets/upload 上傳不支援的副檔名回傳 400。"""
    txt_bytes = b"hello world"
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("test.txt", io.BytesIO(txt_bytes), "text/plain")},
    )
    assert response.status_code == 400
    assert "Only CSV/XLSX/XLS files are supported" in response.json()["detail"]


def test_list_datasets_route(client: TestClient):
    """測試 GET /api/v1/datasets 列表與分頁。"""
    # 先上傳兩份資料集
    for name in ["file1.csv", "file2.csv"]:
        client.post(
            "/api/v1/datasets/upload",
            files={"file": (name, io.BytesIO(b"a,b\n1,2"), "text/csv")},
        )

    # 預設分頁
    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 20

    # 自訂分頁
    p_res = client.get("/api/v1/datasets?page=1&page_size=1")
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert len(p_data["items"]) == 1
    assert p_data["total"] == 2


def test_list_datasets_route_invalid_params(client: TestClient):
    """測試 GET /api/v1/datasets 傳入非法的 page 參數回傳 422。"""
    response = client.get("/api/v1/datasets?page=0")
    assert response.status_code == 422


def test_get_dataset_route_success(client: TestClient):
    """測試 GET /api/v1/datasets/{id} 取得單一資料集。"""
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("target.csv", io.BytesIO(b"x\n10"), "text/csv")},
    )
    dataset_id = upload_res.json()["id"]

    response = client.get(f"/api/v1/datasets/{dataset_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dataset_id
    assert data["filename"] == "target.csv"


def test_get_dataset_route_not_found(client: TestClient):
    """測試 GET /api/v1/datasets/{id} 查無資料回傳 404。"""
    response = client.get("/api/v1/datasets/99999")
    assert response.status_code == 404
    assert "Dataset not found" in response.json()["detail"]


def test_update_dataset_route_success(client: TestClient):
    """測試 PATCH /api/v1/datasets/{id} 更新資料集。"""
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("before.csv", io.BytesIO(b"col\n1"), "text/csv")},
    )
    dataset_id = upload_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/datasets/{dataset_id}",
        json={"filename": "after.csv", "status": "processing"},
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["filename"] == "after.csv"
    assert data["status"] == "processing"


def test_update_dataset_route_not_found(client: TestClient):
    """測試 PATCH /api/v1/datasets/{id} 更新不存在的資料集回傳 404。"""
    patch_res = client.patch(
        "/api/v1/datasets/99999",
        json={"status": "ready"},
    )
    assert patch_res.status_code == 404


def test_delete_dataset_route_success(client: TestClient):
    """測試 DELETE /api/v1/datasets/{id} 成功刪除回傳 204 No Content。"""
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("del.csv", io.BytesIO(b"a\n1"), "text/csv")},
    )
    dataset_id = upload_res.json()["id"]

    del_res = client.delete(f"/api/v1/datasets/{dataset_id}")
    assert del_res.status_code == 204

    # 再次查詢確認已刪除
    get_res = client.get(f"/api/v1/datasets/{dataset_id}")
    assert get_res.status_code == 404


def test_delete_dataset_route_not_found(client: TestClient):
    """測試 DELETE /api/v1/datasets/{id} 刪除不存在的資料集回傳 404。"""
    del_res = client.delete("/api/v1/datasets/99999")
    assert del_res.status_code == 404

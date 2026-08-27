import datetime as dt
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.db import Base, engine, get_db
from sqlalchemy.orm import sessionmaker
from app.models.analysis import AnalysisTask

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Insert placeholder datasets so FK constraints on analysis_tasks are satisfied
    from app.models.dataset import Dataset
    datasets = [
        Dataset(id=1, filename="dummy1.csv", file_path="/tmp/dummy1.csv", row_count=3, column_count=2, status="READY"),
        Dataset(id=2, filename="dummy2.csv", file_path="/tmp/dummy2.csv", row_count=3, column_count=2, status="READY"),
    ]
    db.add_all(datasets)
    db.flush()
    
    # 建立幾筆假任務來測試 LAG 和 ROW_NUMBER
    # 為了測試時間差，設定不同的 started_at 和 completed_at
    base_time = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    
    tasks = [
        AnalysisTask(id=1, dataset_id=1, task_type="descriptive", status="COMPLETED", started_at=base_time, completed_at=base_time + dt.timedelta(seconds=10)),
        AnalysisTask(id=2, dataset_id=1, task_type="correlation", status="COMPLETED", started_at=base_time, completed_at=base_time + dt.timedelta(seconds=15)),
        AnalysisTask(id=3, dataset_id=1, task_type="descriptive", status="COMPLETED", started_at=base_time, completed_at=base_time + dt.timedelta(seconds=12)),
        AnalysisTask(id=4, dataset_id=2, task_type="descriptive", status="COMPLETED", started_at=base_time, completed_at=base_time + dt.timedelta(seconds=20)),
    ]
    
    db.add_all(tasks)
    db.commit()
    db.close()
    
    yield
    with TestingSessionLocal() as cleanup_db:
        from app.models.dataset import DatasetColumn
        from app.models.analysis import AnalysisResult
        cleanup_db.query(AnalysisResult).delete()
        cleanup_db.query(AnalysisTask).delete()
        cleanup_db.query(DatasetColumn).delete()
        cleanup_db.query(Dataset).delete()
        cleanup_db.commit()



def test_pagination_row_number(setup_database):
    # 測試 ROW_NUMBER() 分頁
    # 一次拿 2 筆，測試第 1 頁與第 2 頁
    resp1 = client.get("/api/v1/analysis/tasks?page=1&page_size=2")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["total"] == 4
    assert len(data1["items"]) == 2
    assert data1["items"][0]["id"] == 4  # descending order
    assert data1["items"][1]["id"] == 3
    
    resp2 = client.get("/api/v1/analysis/tasks?page=2&page_size=2")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2["items"]) == 2
    assert data2["items"][0]["id"] == 2
    assert data2["items"][1]["id"] == 1


def test_lag_execution_trend(setup_database):
    # 測試 LAG() 計算任務執行時間趨勢
    resp = client.get("/api/v1/analysis/tasks/trend?dataset_id=1")
    assert resp.status_code == 200
    trends = resp.json()
    
    # Dataset 1 has 3 tasks: id 1 (desc), 2 (corr), 3 (desc)
    assert len(trends) == 3
    
    # 找出 descriptive 類型的任務 (id 1, 3)
    desc_trends = [t for t in trends if t["task_type"] == "descriptive"]
    assert len(desc_trends) == 2
    
    # id 1 是第一筆 descriptive，沒有前一筆
    t1 = next(t for t in desc_trends if t["task_id"] == 1)
    assert t1["execution_time_ms"] == 10000.0  # 10s
    assert t1["prev_execution_time_ms"] is None
    assert t1["time_diff_ms"] is None
    
    # id 3 是第二筆 descriptive，前一筆是 id 1
    t3 = next(t for t in desc_trends if t["task_id"] == 3)
    assert t3["execution_time_ms"] == 12000.0  # 12s
    assert t3["prev_execution_time_ms"] == 10000.0
    assert t3["time_diff_ms"] == 2000.0

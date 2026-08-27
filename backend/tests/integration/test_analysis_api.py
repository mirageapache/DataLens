import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.db import Base, engine, get_db
from sqlalchemy.orm import sessionmaker

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

from app.models.dataset import Dataset, DatasetColumn
from app.models.analysis import AnalysisTask, AnalysisResult

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    with TestingSessionLocal() as db:
        db.query(AnalysisResult).delete()
        db.query(AnalysisTask).delete()
        db.query(DatasetColumn).delete()
        db.query(Dataset).delete()
        db.commit()

from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_celery_task():
    with patch("app.tasks.analysis_tasks.run_analysis_task.delay") as mock_delay:
        mock_delay.return_value.id = "mock-task-id"
        yield mock_delay

@pytest.fixture
def test_csv_file(tmp_path):
    # Create a small CSV file for testing
    csv_path = tmp_path / "test_data.csv"
    with open(csv_path, "w") as f:
        f.write("id,sales,category,date\n1,100,A,2023-01-01\n2,200,B,2023-01-02\n3,150,A,2023-01-03")
    return csv_path

@pytest.mark.parametrize("task_type, payload_extras", [
    ("descriptive", {"target_columns": ["sales"]}),
    ("distribution", {"target_columns": ["sales"]}),
    ("time_series", {"time_column": "date"}),
    ("cross_tabulation", {"cross_tab_index_column": "category", "cross_tab_columns_column": "id"}),
])
def test_analysis_flow(setup_database, test_csv_file, task_type, payload_extras):
    # 1. Upload dataset first
    with open(test_csv_file, "rb") as f:
        upload_resp = client.post("/api/v1/datasets/upload", files={"file": ("test_data.csv", f, "text/csv")})
        
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["id"]

    # 2. Trigger analysis
    run_req = {
        "dataset_id": dataset_id,
        "task_type": task_type,
        **payload_extras
    }
    run_resp = client.post("/api/v1/analysis/run", json=run_req)
    if run_resp.status_code != 200:
        print("run_resp error:", run_resp.text)
    assert run_resp.status_code == 200

    task_data = run_resp.json()
    task_id = task_data["id"]

    # In test environment there is no live Celery worker, so the task is
    # dispatched asynchronously and stays PENDING.
    # We verify the task record was correctly created instead.
    assert task_id > 0
    assert task_data["dataset_id"] == dataset_id
    assert task_data["task_type"] == task_type
    assert task_data["status"] in ("PENDING", "COMPLETED")  # COMPLETED if Celery is live

    # 3. Get task status — should return 200 regardless of completion state
    status_resp = client.get(f"/api/v1/analysis/tasks/{task_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["id"] == task_id

    # 4. Results and charts endpoints should return 200 (may be empty if PENDING)
    results_resp = client.get(f"/api/v1/analysis/tasks/{task_id}/results")
    assert results_resp.status_code == 200

    charts_resp = client.get(f"/api/v1/analysis/tasks/{task_id}/charts")
    assert charts_resp.status_code == 200

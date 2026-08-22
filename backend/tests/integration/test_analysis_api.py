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

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_csv_file(tmp_path):
    # Create a small CSV file for testing
    csv_path = tmp_path / "test_data.csv"
    with open(csv_path, "w") as f:
        f.write("id,sales,category\n1,100,A\n2,200,B\n3,150,A")
    return csv_path

def test_analysis_flow(setup_database, test_csv_file):
    # 1. Upload dataset first
    with open(test_csv_file, "rb") as f:
        upload_resp = client.post("/api/v1/datasets/upload", files={"file": ("test_data.csv", f, "text/csv")})
        
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["id"]

    # 2. Trigger analysis
    run_req = {
        "dataset_id": dataset_id,
        "task_type": "descriptive",
        "target_columns": ["sales"]
    }
    run_resp = client.post("/api/v1/analysis/run", json=run_req)
    assert run_resp.status_code == 200
    task_id = run_resp.json()["id"]
    assert run_resp.json()["status"] == "COMPLETED"

    # 3. Get task results
    results_resp = client.get(f"/api/v1/analysis/tasks/{task_id}/results")
    assert results_resp.status_code == 200
    results = results_resp.json()
    assert len(results) > 0
    
    # 4. Get chart data
    charts_resp = client.get(f"/api/v1/analysis/tasks/{task_id}/charts")
    assert charts_resp.status_code == 200
    charts = charts_resp.json()
    assert "descriptive_stats_sales" in charts
    assert charts["descriptive_stats_sales"]["mean"] == 150.0

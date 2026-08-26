from fastapi.testclient import TestClient
from app.main import app
from app.core.db import Base, engine, get_db
from sqlalchemy.orm import sessionmaker

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

Base.metadata.create_all(bind=engine)
with open("test_data.csv", "w") as f:
    f.write("id,sales,category,date\n1,100,A,2023-01-01\n2,200,B,2023-01-02\n3,150,A,2023-01-03")

upload_resp = client.post("/api/v1/datasets/upload", files={"file": ("test_data.csv", open("test_data.csv", "rb"), "text/csv")})
dataset_id = upload_resp.json()["id"]

run_req = {
    "dataset_id": dataset_id,
    "task_type": "descriptive",
    "target_columns": ["sales"]
}
run_resp = client.post("/api/v1/analysis/run", json=run_req)
print(run_resp.text)

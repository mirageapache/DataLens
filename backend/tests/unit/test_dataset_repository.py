from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset import Dataset, DatasetColumn
from app.repositories.dataset_repository import DatasetRepository


def test_repo_create_dataset_with_columns(db_session: Session):
    """測試 Repository 建立 Dataset 及一對多關聯 DatasetColumn。"""
    repo = DatasetRepository(db_session)
    dataset = Dataset(
        filename="sales.csv",
        file_path="uploads/sales.csv",
        row_count=100,
        column_count=2,
        status="ready",
    )
    col1 = DatasetColumn(
        column_name="amount",
        data_type="numeric",
        null_count=0,
        unique_count=95,
    )
    col2 = DatasetColumn(
        column_name="region",
        data_type="categorical",
        null_count=2,
        unique_count=4,
    )
    dataset.columns = [col1, col2]

    created = repo.create(dataset)

    assert created.id is not None
    assert len(created.columns) == 2
    assert created.columns[0].dataset_id == created.id
    assert created.columns[1].dataset_id == created.id


def test_repo_get_existing_dataset(db_session: Session):
    """測試依 ID 取得 Dataset，並驗證 selectinload 正確預先載入 columns。"""
    repo = DatasetRepository(db_session)
    dataset = Dataset(
        filename="users.csv",
        file_path="uploads/users.csv",
        row_count=50,
        column_count=1,
        status="ready",
    )
    dataset.columns.append(
        DatasetColumn(column_name="user_id", data_type="numeric", null_count=0, unique_count=50)
    )
    repo.create(dataset)

    fetched = repo.get(dataset.id)
    assert fetched is not None
    assert fetched.id == dataset.id
    assert fetched.filename == "users.csv"
    assert len(fetched.columns) == 1
    assert fetched.columns[0].column_name == "user_id"


def test_repo_get_non_existing_dataset(db_session: Session):
    """測試查詢不存在的 ID 回傳 None。"""
    repo = DatasetRepository(db_session)
    result = repo.get(9999)
    assert result is None


def test_repo_list_pagination(db_session: Session):
    """測試分頁查詢與總數計算。"""
    repo = DatasetRepository(db_session)
    for i in range(5):
        dataset = Dataset(
            filename=f"file_{i}.csv",
            file_path=f"uploads/file_{i}.csv",
            row_count=10 * i,
            column_count=2,
            status="ready",
        )
        repo.create(dataset)

    # Page 1 (2 items)
    items_p1, total = repo.list(page=1, page_size=2)
    assert len(items_p1) == 2
    assert total == 5

    # Page 3 (1 item)
    items_p3, total = repo.list(page=3, page_size=2)
    assert len(items_p3) == 1
    assert total == 5

    # Page 4 (0 items)
    items_p4, total = repo.list(page=4, page_size=2)
    assert len(items_p4) == 0
    assert total == 5


def test_repo_update_dataset(db_session: Session):
    """測試更新 Dataset 屬性。"""
    repo = DatasetRepository(db_session)
    dataset = Dataset(
        filename="initial.csv",
        file_path="uploads/initial.csv",
        status="uploaded",
    )
    created = repo.create(dataset)

    created.filename = "updated.csv"
    created.status = "ready"
    updated = repo.update(created)

    assert updated.filename == "updated.csv"
    assert updated.status == "ready"


def test_repo_delete_dataset_cascades_columns(db_session: Session):
    """測試刪除 Dataset 時，關聯的 DatasetColumn 自動級聯刪除。"""
    repo = DatasetRepository(db_session)
    dataset = Dataset(
        filename="to_delete.csv",
        file_path="uploads/to_delete.csv",
        status="ready",
    )
    col = DatasetColumn(column_name="metric", data_type="numeric", null_count=0, unique_count=10)
    dataset.columns.append(col)
    created = repo.create(dataset)
    dataset_id = created.id

    repo.delete(created)

    assert repo.get(dataset_id) is None
    # 檢查 dataset_columns 表內是否已被級聯刪除
    remaining_cols = list(
        db_session.scalars(select(DatasetColumn).where(DatasetColumn.dataset_id == dataset_id))
    )
    assert len(remaining_cols) == 0

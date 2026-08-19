import io
from pathlib import Path
from typing import Generator

import pandas as pd
import pytest
from fastapi import UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base
from app.services.dataset_service import DatasetService


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """建立 SQLite In-Memory 資料庫 Session 供測試使用。"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def temp_upload_dir(tmp_path: Path) -> Path:
    """提供獨立且乾淨的暫存上傳目錄。"""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


@pytest.fixture
def dataset_service(db_session: Session, temp_upload_dir: Path) -> DatasetService:
    """提供已配置暫存目錄與 In-Memory DB 的 DatasetService 實例。"""
    service = DatasetService(db=db_session)
    service.upload_root = temp_upload_dir
    return service


@pytest.fixture
def make_csv_upload_file():
    """工廠 fixture：生成 CSV UploadFile。"""
    def _create(content: str, filename: str = "test.csv") -> UploadFile:
        file_bytes = content.encode("utf-8")
        return UploadFile(file=io.BytesIO(file_bytes), filename=filename)
    return _create


@pytest.fixture
def make_excel_upload_file():
    """工廠 fixture：生成 Excel (.xlsx) UploadFile。"""
    def _create(df: pd.DataFrame, filename: str = "test.xlsx") -> UploadFile:
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        return UploadFile(file=buffer, filename=filename)
    return _create


@pytest.fixture
def client(db_session: Session, temp_upload_dir: Path, monkeypatch) -> Generator:
    """FastAPI TestClient 測試夾具，自動注入測試 DB 與暫存目錄。"""
    from fastapi.testclient import TestClient
    from app.core.db import get_db
    from app.main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    original_init = DatasetService.__init__

    def _patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.upload_root = temp_upload_dir

    monkeypatch.setattr(DatasetService, "__init__", _patched_init)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

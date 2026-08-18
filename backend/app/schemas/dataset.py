import datetime as dt

from pydantic import BaseModel, Field


class DatasetColumnRead(BaseModel):
    """單一資料欄位的回傳模型（對應 dataset_columns 的一列）。"""

    id: int
    column_name: str
    data_type: str
    null_count: int | None
    unique_count: int | None

    # 讓 Pydantic 可以直接從 SQLAlchemy ORM 物件轉成 schema。
    model_config = {"from_attributes": True}


class DatasetRead(BaseModel):
    """單一資料集的完整回傳模型（含欄位統計資訊）。"""

    id: int
    filename: str
    file_path: str
    row_count: int | None
    column_count: int | None
    status: str
    created_at: dt.datetime
    # default_factory 可避免可變預設值帶來的共享狀態問題。
    columns: list[DatasetColumnRead] = Field(default_factory=list)

    # 讓 Dataset ORM 物件可直接被 model_validate() 序列化。
    model_config = {"from_attributes": True}


class DatasetListResponse(BaseModel):
    """資料集列表 API 的回應模型（含分頁資訊）。"""

    items: list[DatasetRead]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class DatasetUpdate(BaseModel):
    """資料集更新請求模型（PATCH，可部分更新）。"""

    status: str | None = None
    filename: str | None = None

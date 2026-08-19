# DataLens Backend

> DataLens 的後端核心服務 — 基於 **FastAPI** + **SQLAlchemy 2.0** + **PostgreSQL** 的高效能資料分析與管理平台 API。

---

## 📌 目錄

- [專案簡介](#-專案簡介)
- [技術堆疊](#-技術堆疊)
- [架構設計與目錄結構](#-架構設計與目錄結構)
- [快速開始](#-快速開始)
  - [環境需求](#環境需求)
  - [本機安裝與設定](#本機安裝與設定)
  - [資料庫遷移 (Alembic)](#資料庫遷移-alembic)
  - [啟動開發伺服器](#啟動開發伺服器)
- [API 端點說明](#-api-端點說明)
- [自動化測試](#-自動化測試)
- [Docker 容器化部署](#-docker-容器化部署)

---

## 📖 專案簡介

DataLens 後端提供結構化資料（CSV / Excel）的匯入、欄位型別自動偵測、統計特徵計算以及完整的 Dataset CRUD 管理功能，並為未來的非同步任務排程（Celery）與統計分析引擎提供穩固的基礎設施。

### 核心功能 (Phase 1)
- **檔案解析與欄位推斷**：支援 `.csv`、`.xlsx`、`.xls` 上傳，自動辨識數值 (`numeric`)、日期時間 (`datetime`) 與類別 (`categorical`) 欄位。
- **資料特徵統計**：自動計算資料集維度（列數/欄數）、欄位缺值數 (`null_count`) 與唯一值個數 (`unique_count`)。
- **嚴格的分層架構**：依循 SOLID 原則，實作 Router / Service / Repository / Schema / Model 分層設計。
- **自動化檔案管理**：檔案寫入與交易一致性，解析失敗或刪除資料集時自動清理實體檔案。

---

## 🛠 技術堆疊

| 領域 | 技術組件 | 說明 |
| :--- | :--- | :--- |
| **程式語言** | Python 3.13+ | 使用最新 Python 特性與型別標註 |
| **Web 框架** | FastAPI 0.141+ | 高效能非同步 Web 框架，自動生成 OpenAPI 文件 |
| **ORM / 資料庫** | SQLAlchemy 2.0 + PostgreSQL (`psycopg`) | 現代化 ORM 與連線池管理 |
| **資料庫遷移** | Alembic | 資料庫版本控管與 Schema Migration |
| **資料處理** | pandas + openpyxl | 高效能資料表解析與統計推斷 |
| **非同步佇列** | Celery + Redis | 大檔案非同步處理與任務排程（後續階段） |
| **測試框架** | pytest + pytest-cov + httpx | 支援 In-Memory SQLite 快速單元與路由整合測試 |

---

## 🏗 架構設計與目錄結構

採用嚴格的三層式架構（Layered Architecture），確保各層職責單一且具備高可測試性（Dependency Inversion）：

```
backend/
├── alembic/                  # Alembic 資料庫遷移腳本與版本記錄
│   ├── versions/
│   └── env.py
├── alembic.ini               # Alembic 配置檔
├── app/
│   ├── core/                 # 核心配置（環境變數、資料庫連線 Session 管理）
│   │   ├── config.py
│   │   └── db.py
│   ├── models/               # SQLAlchemy ORM 資料表模型 (Domain Models)
│   │   └── dataset.py
│   ├── repositories/         # 資料庫存取層 (Repository Pattern，隔離 ORM 語法)
│   │   └── dataset_repository.py
│   ├── routes/               # API 路由層 (FastAPI 請求分派與 HTTP 驗證)
│   │   └── datasets.py
│   ├── schemas/              # Pydantic 資料模型 (DTO，負責 Request/Response 序列化)
│   │   └── dataset.py
│   ├── services/             # 核心業務邏輯層 (Business Logic)
│   │   └── dataset_service.py
│   ├── tasks/                # Celery 非同步背景任務 (即將實作)
│   └── main.py               # FastAPI 應用程式進入點
├── tests/                    # 自動化測試套件
│   ├── conftest.py           # 共享 Fixtures (In-Memory DB、TestClient、檔案生成器)
│   └── unit/
│       ├── test_dataset_repository.py  # DB 存取層測試
│       ├── test_dataset_schemas.py     # Pydantic 驗證測試
│       ├── test_dataset_service.py     # 業務邏輯與資料解析測試
│       └── test_datasets_routes.py     # HTTP 端點整合測試
├── Dockerfile                # 後端容器構建檔
├── pyproject.toml            # 專案相依套件與建置設定
└── README.md
```

---

## 🚀 快速開始

### 環境需求
- Python `>= 3.13`
- PostgreSQL 17+（本機或 Docker）
- Redis 7+（非同步任務用）

### 本機安裝與設定

1. **建立並啟用虛擬環境**：
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate  # macOS / Linux
   # 或 .venv\Scripts\activate  # Windows
   ```

2. **安裝專案與開發相依套件**：
   ```bash
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```

3. **配置環境變數**：
   專案根目錄備有 `.env.example`，請於專案根目錄建立 `.env` 檔案：
   ```ini
   APP_NAME="DataLens API"
   DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/datalens"
   REDIS_URL="redis://localhost:6379/0"
   ```

### 資料庫遷移 (Alembic)

在啟動服務前，確保資料庫已建立並套用最新的 Migration：

```bash
# 執行所有尚未套用的遷移
alembic upgrade head

# 若有修改 models，自動產生新的遷移腳本
alembic revision --autogenerate -m "describe your changes"
```

### 啟動開發伺服器

使用 FastAPI 內建的熱重載開發伺服器：

```bash
fastapi dev app/main.py
# 或使用 uvicorn
uvicorn app.main:app --reload --port 8000
```

服務啟動後，可開啟瀏覽器存取互動式 API 文件：
- **Swagger UI**：[http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**：[http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 API 端點說明

目前已實作的 API 端點（Prefix: `/api/v1`）：

| HTTP Method | Endpoint | 說明 | 成功狀態碼 |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | 系統健康檢查 | `200 OK` |
| `POST` | `/api/v1/datasets/upload` | 上傳資料集（multipart/form-data，支援 CSV/Excel） | `201 Created` |
| `GET` | `/api/v1/datasets` | 取得資料集列表（支援 `page`, `page_size` 分頁） | `200 OK` |
| `GET` | `/api/v1/datasets/{id}` | 查詢指定資料集詳細資訊（含所有欄位型別與統計） | `200 OK` |
| `PATCH` | `/api/v1/datasets/{id}` | 更新資料集資訊（部分更新 `filename`, `status`） | `200 OK` |
| `DELETE` | `/api/v1/datasets/{id}` | 刪除資料集（一併清除資料庫記錄與實體儲存檔案） | `204 No Content` |

---

## 🧪 自動化測試

本專案使用 `pytest` 進行單元與整合測試。測試時自動透過 In-Memory SQLite 模擬資料庫，無需啟動實體 PostgreSQL。

### 執行測試方式

請確保已**啟用虛擬環境**或直接使用 `.venv` 內的 pytest：

#### 方式 1：啟用虛擬環境後執行（推薦）
```bash
# 位於 backend 目錄下
source .venv/bin/activate

# 執行所有測試
pytest -v

# 執行測試並產生覆蓋率報告
pytest --cov=app --cov-report=term-missing -v
```

#### 方式 2：直接指定虛擬環境路徑執行
```bash
.venv/bin/pytest --cov=app --cov-report=term-missing -v
```

#### 方式 3：在 Docker 容器內執行測試
```bash
docker compose exec fastapi-app uv run pytest --cov=app --cov-report=term-missing -v
```

當前測試指標：
- **測試案例數**：41 Passed
- **程式碼覆蓋率**：98%（`app/services/dataset_service.py` 達 100%）

---

## 🐳 Docker 容器化部署

可透過專案根目錄的 `docker-compose.yml` 統一啟動包含 PostgreSQL、Redis 與 FastAPI 的完整環境：

```bash
# 從專案根目錄啟動所有服務
docker compose up -d --build

# 查看容器日誌
docker compose logs -f fastapi-app
```

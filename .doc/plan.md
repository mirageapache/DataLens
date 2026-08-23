# DataLens — 資料分析與系統監控整合平台

> 讓任何人都能對數據提問並獲得洞察的後端驅動資料分析平台。

| 項目 | 內容 |
|------|------|
| 版本 | v1.0 |
| 建立日期 | 2026 年 5 月 |
| 預計開發期 | 8 ～ 10 週 |

---

## 目錄

1. [專案概觀](#1-專案概觀)
2. [技術架構](#2-技術架構)
3. [功能設計](#3-功能設計)
4. [後端架構設計](#4-後端架構設計)
5. [資料庫設計](#5-資料庫設計)
6. [DevOps 與監控設計](#6-devops-與監控設計)
7. [開發路線圖](#7-開發路線圖)
8. [Repository 結構](#8-repository-結構)
9. [風險評估](#9-風險評估)

---

## 1. 專案概觀

使用者可上傳 CSV / Excel 等結構化資料，系統自動執行統計分析、產生視覺化報表，並提供 REST API 供前端或外部系統串接。

**核心功能概念：**

- 支援任意結構化資料匯入（CSV、Excel）
- 自動執行描述性統計、相關性分析、分組聚合
- 非同步任務處理大型資料集，前端即時輪詢進度
- Grafana Dashboard 監控系統健康度與任務狀態
- Angular 前端提供互動式視覺化 Dashboard

---

## 2. 技術架構

### 2.1 技術選型總覽

| 層級 | 技術 | 說明 |
|------|------|------|
| 後端框架 | Python 3.13.6 + FastAPI | 輕量高效能，原生 async 支援 |
| 主資料庫 | PostgreSQL (Supabase) | 資料庫 SQL 設計實作 |
| 非同步任務 | Celery + Redis | 大檔案背景處理，任務狀態追蹤 |
| 監控 / 日誌 | Grafana + Loki | 系統健康度看板、Log 查詢 |
| 容器化 | Docker + Docker Compose | 所有服務統一管理，一鍵啟動 |
| 前端框架 | Angular 21 + TypeScript | 元件化開發 |
| 資料視覺化 | ECharts（ngx-echarts） | 動態互動圖表 |
| API 文件 | FastAPI Swagger UI | 自動產生，開發友善 |

### 2.2 系統架構概述

```
┌─────────────────────────────────────────────┐
│                  用戶端層                     │
│         Angular 21 SPA（前端）                │
└───────────────────┬─────────────────────────┘
                    │ HTTP / REST
┌───────────────────▼─────────────────────────┐
│                 API 閘道層                   │
│    FastAPI（請求驗證、路由分派、Log 輸出）     │
└──────┬──────────────────────────────┬────────┘
       │                              │
┌──────▼──────┐              ┌────────▼────────┐
│  PostgreSQL │              │  Redis + Celery  │
│  (Supabase) │              │  非同步任務佇列   │
└─────────────┘              └─────────────────┘
       │                              │
┌──────▼──────────────────────────────▼────────┐
│              監控與可觀測性層                   │
│         Grafana + Loki（Log 聚合）             │
└───────────────────────────────────────────────┘
```

---

## 3. 功能設計

### 3.1 模組 A｜資料匯入

- 支援 CSV、XLSX 檔案上傳（單檔上限 50 MB）
- 欄位型別自動偵測（數值 / 類別 / 日期）
- 資料驗證：缺值比例、欄位一致性檢查，回傳結構化錯誤報告
- 大檔案（> 5 MB）轉非同步任務（Celery），前端輪詢任務狀態

### 3.2 模組 B｜統計分析引擎

- **描述性統計**：mean、median、std、quartile、skewness、kurtosis
- **相關性分析**：Pearson / Spearman 相關矩陣，Heat Map 輸出
- **分組聚合**：GROUP BY 任意欄位，支援 SUM / AVG / COUNT / MAX / MIN
- **時序分析**：若資料含日期欄位，自動產生趨勢折線圖
- 分析結果持久化至 PostgreSQL（Supabase），支援歷史紀錄查詢

### 3.3 模組 C｜視覺化 Dashboard

- Angular 前端 + ngx-echarts 動態渲染
- 圖表類型：長條圖、折線圖、散佈圖、熱力圖、圓餅圖
- 支援圖表設定客製化（軸標籤、顏色、資料範圍篩選）
- 分析報告匯出：PDF / CSV 格式下載

### 3.4 模組 D｜系統監控

- API 吞吐量（req/min）、平均回應時間、錯誤率趨勢
- Celery 任務佇列深度、成功 / 失敗比例
- 結構化 Log 接入 Loki，支援 LogQL 關鍵字查詢
- Dashboard 包含：系統健康度總覽、任務執行歷史、錯誤日誌 Panel

### 3.5 API 端點設計

| Method | Endpoint | 說明 |
|--------|----------|------|
| POST | `/api/v1/datasets/upload` | 上傳並解析資料集 |
| GET | `/api/v1/datasets` | 列出所有資料集（列表頁用，支援分頁）|
| GET | `/api/v1/datasets/{id}` | 查詢資料集詳細資訊（含欄位描述）|
| POST | `/api/v1/analysis/run` | 觸發分析任務，回傳 `task_id` |
| GET | `/api/v1/analysis/tasks` | 列出分析任務歷史（可依 `dataset_id` 篩選）|
| GET | `/api/v1/analysis/tasks/{task_id}` | 查詢非同步任務狀態 |
| GET | `/api/v1/analysis/tasks/{task_id}/results` | 取得分析結果（含統計數據） |
| GET | `/api/v1/analysis/tasks/{task_id}/charts` | 取得圖表所需 JSON 資料 |
| GET | `/api/v1/health` | 系統健康度檢查 |

> **範圍說明**：本期為作品集專案，不實作認證 / 授權；API 預設運行於受信任的本地 / 內網環境。若日後對外開放，再補 API Key 或 JWT。

---

## 4. 後端架構設計

### 4.1 OOP 分層架構

採用嚴格三層分離，每個類別只有單一職責：

| 層次 | 目錄 | 職責 |
|------|------|------|
| Router Layer | `routes/` | 處理 HTTP 請求驗證、路由分派，不含業務邏輯 |
| Service Layer | `services/` | 業務邏輯核心，透過建構子注入 Repository（便於測試 mock） |
| Repository Layer | `repositories/` | 所有 DB 操作集中於此，Service 不直接接觸 ORM |
| Schema Layer | `schemas/` | Pydantic 資料模型，負責輸入驗證與輸出序列化 |
| Domain Layer | `models/` | SQLAlchemy ORM 模型定義，映射資料庫結構 |

### 4.2 SOLID 原則實踐重點

- **Single Responsibility**：`AnalysisService` 只負責分析邏輯；`DatasetRepository` 只負責 DB 存取。
- **Open/Closed**：分析策略（`StatisticalAnalyzer`）設計為抽象類別，新增分析類型無需修改既有程式碼。
- **Dependency Inversion**：Service 透過建構子注入具體 Repository，測試時注入 mock 即可；不為「換資料庫」預留抽象介面（單一 Postgres，避免過度設計）。

### 4.3 目錄結構

```
backend/
├── app/
│   ├── routes/          # Router Layer
│   ├── services/        # Service Layer
│   ├── repositories/    # Repository Layer
│   ├── schemas/         # Pydantic Models
│   ├── models/          # SQLAlchemy ORM
│   ├── tasks/           # Celery 非同步任務
│   └── core/            # 設定、DB 連線、middleware
└── tests/               # Unit + Integration Tests
```

---

## 5. 資料庫設計

### 5.1 核心資料表

| 資料表 | 用途 | 主要欄位 |
|--------|------|----------|
| `datasets` | 資料集主表 | id, filename, row_count, column_count, status, created_at, file_path |
| `dataset_columns` | 欄位描述 | id, dataset_id (FK), column_name, data_type, null_count, unique_count |
| `analysis_tasks` | 分析任務 | id, dataset_id (FK), task_type, celery_task_id, status, started_at, completed_at |
| `analysis_results` | 分析結果 | id, task_id (FK), metric_name, metric_value, chart_data (JSONB) |
| `system_logs` | 結構化請求日誌落庫（供 SQL 聚合 + Grafana Postgres 資料源查詢，與 Loki 互補） | id, level, message, endpoint, duration_ms, created_at |

### 5.2 進階 SQL 實作重點

- **Window Function**：使用 `ROW_NUMBER()` 實作分頁查詢；`LAG()` 計算任務執行時間趨勢。
- **Index 設計**：為 `dataset_id`、`status`、`created_at` 建立複合索引，並撰寫效能分析對比。
- **Stored Procedure**：封裝報表匯出的複雜聚合查詢。
- **Transaction**：檔案上傳流程使用顯式 Transaction，確保資料集與欄位描述同時寫入或回滾。

---

## 6. DevOps 與監控設計

### 6.1 Docker Compose 服務清單

| 服務 | 用途 | Port | 備註 |
|------|------|------|------|
| `fastapi-app` | FastAPI 應用本體 | 8000 | 熱重載開發模式；上傳檔案寫入共用 `uploads` volume |
| `postgres` | PostgreSQL 17（本地開發用） | 5432 | 資料持久化至 volume，Supabase 用於雲端 |
| `redis` | Celery Message Broker | 6379 | 任務佇列 |
| `celery-worker` | 非同步任務執行器 | — | 共享 fastapi-app 程式碼**與 `uploads` volume**（否則讀不到上傳檔） |
| `grafana` | 監控 Dashboard | 3000 | 匯入預設 Dashboard JSON |
| `loki` | Log 聚合 | 3100 | 接收 FastAPI 結構化 Log |
| `promtail` | Log 收集器 | — | 讀取 Docker log 轉發至 Loki |

> **共用檔案儲存**：`fastapi-app` 與 `celery-worker` 是獨立容器、檔案系統不共通。上傳檔案必須放在兩者都掛載的 named volume（例：`uploads:/app/uploads`），worker 才讀得到 `datasets.file_path`。本地開發用共用 volume 即可；未來要多台 worker 或上雲，再改存物件儲存（Supabase Storage / S3，`file_path` 改存 URL）。
>
> ```yaml
> volumes:
>   uploads:
> services:
>   fastapi-app:
>     volumes: [uploads:/app/uploads]
>   celery-worker:
>     volumes: [uploads:/app/uploads]
> ```

### 6.2 Grafana Dashboard 設計

三個 Panel 群組：

**系統總覽（Overview）**｜資料源：PostgreSQL（`system_logs`）
- API 請求量趨勢（依時間桶 `COUNT`）
- P95 Latency（`percentile_cont(0.95) WITHIN GROUP (ORDER BY duration_ms)`）
- HTTP 錯誤率（依 `status_code` 分組，4xx / 5xx 分佈）

**任務監控（Task Monitor）**｜資料源：PostgreSQL（`analysis_tasks`）
- 佇列深度（`COUNT WHERE status IN ('PENDING','STARTED')`）
- 任務成功率（依 `status` 分組）
- 平均處理時長（`completed_at - started_at`，依任務類型分組）

**日誌分析（Log Explorer）**
- **Loki 資料源**：原始容器 / 應用 log，用 LogQL 按 Log Level（ERROR / WARN / INFO）過濾、Endpoint 關鍵字搜尋
- **PostgreSQL 資料源**：以 `system_logs` 做 SQL 聚合 panel（各 endpoint 錯誤率、平均 `duration_ms`、最慢端點排行），展示 Grafana 接 SQL 資料源的操作

### 6.3 結構化 Log 格式

所有 API 請求輸出 JSON 格式日誌：

```json
{
  "timestamp": "2026-05-01T10:00:00Z",
  "level": "INFO",
  "endpoint": "/api/v1/analysis/run",
  "method": "POST",
  "status_code": 200,
  "duration_ms": 142,
  "error_detail": null
}
```

---

## 7. 開發路線圖

### Phase 1｜後端基礎建設（第 1 ～ 2 週）

- [✅] 初始化專案結構（FastAPI + SQLAlchemy + Alembic）
- [✅] Docker Compose 配置：PostgreSQL + Redis + FastAPI
- [✅] 設計並建立 DB Schema，執行初始 Migration
- [✅] 實作 Dataset 上傳 API（同步版本），完成基本 CRUD
- [✅] 撰寫第一批 Unit Test（pytest）覆蓋資料驗證邏輯

**里程碑 M1**：後端 API + DB 可運行，Docker Compose 一鍵啟動

---

### Phase 2｜分析引擎與非同步任務（第 3 ～ 4 週）

- [✅] 整合 pandas 實作統計分析模組
- [✅] Celery 整合：大檔案分析改為非同步任務，前端輪詢狀態
- [✅] 分析結果序列化並儲存至 PostgreSQL，實作 Window Function 查詢
- [✅] 完成分析結果 API（含圖表 JSON 輸出格式）
- [✅] 撰寫 Integration Test 覆蓋完整分析流程

**里程碑 M2**：分析引擎完成，非同步任務正常運作

---

### Phase 3｜前端開發（第 5 ～ 7 週）

- [✅] 步驟 1：前端專案初始化與 Docker 化環境建置（Angular 21 + TailwindCSS + docker-compose 整合）
- [✅] 步驟 2：核心佈局 (Layout) 與路由 (Routing) 建立（切分共用 Header / Navbar）
- [✅] 步驟 3：後端 API 服務串接 (Service Layer 實作)
- [✅] 步驟 4：實作資料上傳與列表頁（支援單檔 50 MB 限制與拖曳上傳）
- [✅] 步驟 5：實作分析任務狀態與輪詢頁面（RxJS 輪詢機制）
- [✅] 步驟 6：實作圖表與結果頁面（整合 ngx-echarts 渲染至少三種圖表）
- [ ] 步驟 7：加入結構化 Log Middleware 至 FastAPI，並寫入 `system_logs` 資料庫表

**里程碑 M3**：前端 Dashboard 上線，可完整走完「上傳 → 分析 → 視覺化」

---

### Phase 4｜監控、品質提升與收尾（第 8 ～ 10 週）

- [ ] 配置 Loki + Promtail，完成 Log 收集管線
- [ ] 建立 Grafana Dashboard（三個 Panel 群組，Loki + PostgreSQL 雙資料源）
- [ ] 自動化測試：Unit / Integration 覆蓋率目標 > 70%
- [ ] PostgreSQL Index 優化，撰寫優化前後效能對比
- [ ] 完善 README：架構圖、本地啟動指南、技術決策說明（ADR）
- [ ] 整理 GitHub commit history，確保功能有對應 Issue 與 PR

**里程碑 M4**：監控上線、測試覆蓋完整，README 齊備

---

## 8. Repository 結構

採用 Monorepo，單一 GitHub Repository 包含前後端：

```
datalens/
├── docker-compose.yml
├── README.md
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/                  # DB Migration
│   └── app/
│       ├── main.py
│       ├── core/                 # 設定、DB 連線、middleware
│       ├── routes/               # Router Layer
│       ├── services/             # Service Layer
│       ├── repositories/         # Repository Layer
│       ├── schemas/              # Pydantic Models
│       ├── models/               # SQLAlchemy ORM
│       └── tasks/                # Celery Tasks
│   └── tests/
│       ├── unit/
│       └── integration/
│
├── frontend/
│   ├── Dockerfile
│   └── (Angular 21 專案)
│
├── monitoring/
│   ├── grafana/
│   │   └── dashboards/           # Dashboard JSON 設定
│   └── loki/
│       └── loki-config.yml
│
└── docs/
    ├── adr/                      # Architecture Decision Records
    └── api-spec.md
```

---

## 9. 風險評估

| 風險項目 | 程度 | 緩解策略 |
|----------|------|----------|
| Angular 學習曲線 | 高 | 優先學習 Component / Service / HttpClient 三個核心概念，其餘漸進補充 |
| ngx-echarts 與 Angular 21 相容性 | 中 | 開發前先確認 ngx-echarts 最新版是否支援 Angular 21，若不支援改用原生 echarts.init() 整合 |
| Celery + Redis 整合複雜度 | 中 | Phase 2 先實作同步版分析，邏輯確認後再替換為非同步 |
| 專案範疇蔓延 | 中 | 嚴格使用 GitHub Projects 管理 Issue，新想法進 Backlog，本期不增加 MVP 功能 |

---

## 附錄：啟動前準備清單

- [ ] 建立 GitHub Repository（名稱：`datalens`），初始化 README 與 `.gitignore`
- [ ] 在 GitHub Projects 建立 Kanban 看板，將 Phase 1 所有 Issue 建立完畢
- [ ] 本地安裝 Docker Desktop，驗證 PostgreSQL + Redis 容器可正常啟動
- [ ] 建立 FastAPI 專案骨架，確認分層目錄結構
- [ ] 完成第一個 API：`POST /api/v1/datasets/upload`（同步版），附 pytest 測試

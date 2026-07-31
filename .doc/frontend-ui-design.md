# DataLens — 前端 UI 設計文件

> 依 [plan.md](plan.md) 的功能與 API 規劃，定義前端需要的畫面、UI 功能與共用模式。

| 項目 | 內容 |
|------|------|
| 框架 | Angular 21 + TypeScript |
| UI 元件庫 | Angular Material |
| 圖表 | ECharts（ngx-echarts） |
| 導覽模型 | 側邊欄 App Shell |
| 主題 | Light 單一主題（MVP）；dark 之後以 Material theming 加，屬選配 |

> **實作路線**：一律用**真 Angular Material 元件**（`mat-table` / `mat-dialog` / `mat-paginator` 等）。`ui-prototype/` 的三個 HTML 是 Tailwind 仿 Material 的**視覺 / UX 參考**，不逐字移植 Tailwind class。

---

## 1. 資訊架構 / App Shell

```
┌────────────────────────────────────────────────┐
│ ☰  DataLens                     [上傳資料] ⟳ ⚙ │  ← mat-toolbar（⟳=背景任務指示器，選配）
├──────────┬─────────────────────────────────────┤
│ 📁 資料集 │                                     │
│ 📊 分析   │          router-outlet              │  ← mat-sidenav
│ 📈 監控 ↗ │        （各頁面內容）                │
│ 📄 API ↗  │                                     │
└──────────┴─────────────────────────────────────┘
```

- **左側 `mat-sidenav`**：資料集、分析、監控、API。
  - 「監控 ↗」開新分頁到 Grafana，「API ↗」開新分頁到 Swagger UI——兩者皆不在 Angular 內實作，只放外部連結。
- **頂部 `mat-toolbar`**：品牌名、全域「上傳資料」CTA、設定。背景任務指示器（⟳）為選配，見 §2.2。
- 手機版側欄自動收合（`mat-sidenav` responsive mode）。

### 路由總表

| 路由 | 畫面 | 說明 |
|------|------|------|
| `/datasets` | 資料集列表 | 預設首頁 |
| `/datasets/:id` | 資料集詳情 | 含欄位描述、資料品質、**此資料集的歷史分析** |
| `/datasets/:id/analyze` | 分析設定 | dialog 或獨立頁 |
| `/analysis` | **分析歷史列表** | 跨資料集的所有分析任務 |
| `/analysis/tasks/:taskId` | 任務檢視 / 結果 | **單頁兩態**：進行中顯示進度，完成顯示結果 Dashboard |

> **路由簡化**：不設獨立的「進度過渡頁」。點擊分析後直接進 `/analysis/tasks/:taskId`，若 `status` 為 `PENDING/STARTED` 就顯示 Skeleton/Progress 並輪詢，成功後原地切換為圖表 Dashboard。

---

## 2. 畫面規格

### 2.1 資料集列表（`/datasets`）

- **用途**：所有已上傳資料集的入口。
- **UI**：`mat-table`（欄位：檔名、列數、欄數、狀態 chip、建立時間、操作），`mat-paginator` + `mat-sort`；右上「上傳資料」按鈕。
- **狀態**：
  - loading → skeleton rows。
  - empty → **具設計感的 SVG 插圖 + 行動按鈕**「上傳你的第一份 CSV/Excel」。
  - error → `mat-snackbar`。
- **背景任務可見性**：非同步處理中的資料集以 `processing` 狀態 chip 出現在此列表——列表本身即背景任務的主要指示器。
- **API**：`GET /api/v1/datasets`（分頁）。

### 2.2 上傳（`mat-dialog`）

- **用途**：上傳並觸發解析。
- **UI**：
  - 拖放區 + 檔案選擇器（`accept=".csv,.xlsx"`），標示支援格式與 50MB 上限。
  - **拖放視覺回饋**：hover 時虛線邊框變色、放開檔案時的過場動畫。
  - **前端先驗**副檔名與 50MB 上限，過關才送出。
- **非同步（檔案 > 5MB）**：觸發 Celery 後**立即關閉 Dialog**，右下角 `mat-snackbar` 提示「檔案處理中…」。使用者不需死守 Dialog；該資料集會以 `processing` chip 出現在列表（§2.1）。
  - toolbar 的背景任務指示器（⟳ badge）為**選配加分項**，非 MVP 必需——列表 chip 已覆蓋主要需求。
- **驗證錯誤**：後端回傳的結構化錯誤（缺值比例、欄位不一致）以 `mat-expansion-panel` 呈現；錯誤區設 `max-height + overflow-y:auto` 避免撐長 Dialog。（錯誤量普遍很大時，再升級為 `mat-table` + 分頁的「錯誤欄位 vs 原因」表。）
- **API**：`POST /api/v1/datasets/upload`。

### 2.3 資料集詳情（`/datasets/:id`）

- **用途**：檢視單一資料集的結構、品質與歷史分析。
- **UI**（建議以 `mat-tabs` 分「結構」與「歷史分析」兩頁）：
  - **結構頁**：
    - 標頭：檔名、列/欄數、狀態、上傳時間。
    - 欄位表：欄名、型別 chip（數值 / 類別 / 日期）、缺值數、唯一值數。
    - 資料品質：各欄缺值比例橫條。
    - CTA：「執行分析」→ 開分析設定。
  - **歷史分析頁**：此資料集過去的分析任務列表（類型、狀態、時間），點擊導向 `/analysis/tasks/:taskId`。
- **API**：`GET /api/v1/datasets/{id}`（含欄位描述）、`GET /api/v1/analysis/tasks?dataset_id={id}`。

### 2.4 分析設定（`/datasets/:id/analyze` 或 dialog）

- **用途**：設定並觸發分析任務。
- **UI**：先選分析類型，再依類型顯示動態表單：
  | 類型 | 表單欄位 |
  |------|----------|
  | 描述性統計 | 選數值欄位（預設全選） |
  | 相關性分析 | Pearson / Spearman、選欄位 |
  | 分組聚合 | group 欄位 + 聚合欄位 + 函數（SUM/AVG/COUNT/MAX/MIN） |
  | 時序分析 | 日期欄位 + 值欄位 |
  - 可用 `mat-stepper` 分「選類型 → 設參數 → 確認」三步（選配）。
- **型別聯動（重要）**：所有 `mat-select` 依 `GET /datasets/{id}` 的 `dataset_columns` 型別**自動過濾**：
  - 時序的「時間軸」只列 `DATE/DATETIME` 欄位；「值欄位」只列 `NUMERIC`。
  - 分組聚合的聚合欄位只列 `NUMERIC`（COUNT 除外）。
- **預防無效操作**：若資料集缺少某類型所需欄位，該分析類型設 `disabled` 並顯示提示（例：「此資料集未包含日期型別欄位」停用時序分析）。
- **送出**：`POST /api/v1/analysis/run` → 取得 `task_id` → 導向 `/analysis/tasks/:taskId`。

### 2.5 任務檢視 / 分析結果（`/analysis/tasks/:taskId`）

單一頁面、兩種狀態：

- **進行中（`PENDING/STARTED`）**：`mat-progress-bar`（indeterminate）+ 狀態文字，每 ~2s 輪詢；失敗顯示 `error_detail` + 「重試」。
- **完成（`SUCCESS`）**：原地切換為結果視圖。**一個 task 對應單一分析類型**，依該類型渲染對應的統計表 + 圖表（非固定多分頁；prototype `results.html` 的三分頁僅為展示各圖型）：
  | 類型 | 呈現 |
  |------|------|
  | 描述性統計 | 統計表（mean/median/std/quartile/skew/kurtosis）**＋ 直方圖 / 箱形圖**（連續型欄位分佈，標準呈現非選配） |
  | 相關性 | 熱力圖（多欄位處理見 §3） |
  | 分組聚合 | 長條圖 + 資料表 |
  | 時序 | 折線圖 |
  - **圖表控制面板**（每張圖右上，`mat-menu` / `mat-button-toggle`）：切換「顯示數值標籤」、**下載圖片**（ECharts 原生 `toolbox.saveAsImage`，近乎免費）、軸標籤 / 顏色 / 資料範圍篩選（輕量，非完整圖表產生器）。
  - 匯出：整份報告 PDF / CSV 下載。
- **API**：`GET /api/v1/analysis/tasks/{task_id}`（狀態）、`.../results`、`.../charts`。

### 2.6 分析歷史列表（`/analysis`）

- **用途**：跨資料集檢視所有做過的分析任務。
- **UI**：`mat-table`（資料集、分析類型、狀態 chip、建立時間、操作），`mat-paginator` + `mat-sort` + 依狀態/類型篩選；點列導向 `/analysis/tasks/:taskId`。
- **API**：`GET /api/v1/analysis/tasks`（分頁、可篩選）。

---

## 3. 圖表（ngx-echarts）

- **必備三型**：相關性 → 熱力圖；分組聚合 → 長條圖；時序 → 折線圖。
- **描述性分佈**：直方圖 / 箱形圖，**標準呈現**（避免結果頁只有表格略顯單調）。
- **備用**：散佈圖、圓餅圖。
- **熱力圖多欄位處理**：欄位多（約 ≥ 20~30）時會擠成一團——提供「欄位選擇（最少/最多）」或容器 X/Y 軸可捲動（scrollable container），避免壓縮到無法閱讀。
- 配色與可及性於實作階段依 dataviz 規範定義，本文件不綁定色票。

---

## 4. 跨頁共用模式

- **輪詢 service**：以 RxJS `interval + switchMap + takeWhile` 封裝一次，任務檢視頁與大檔上傳共用。
- **狀態 chip 對照**：資料集（uploaded / processing / ready / failed）與任務（PENDING / STARTED / SUCCESS / FAILURE）各一份集中的顏色對照。
- **三態處理**：每個列表 / 區塊都有 loading（skeleton / spinner）、empty、error（`mat-snackbar` + inline 驗證）。
- **HTTP 錯誤攔截**：以 Angular `HttpInterceptor` 統一處理錯誤提示。

---

## 5. Angular Material 元件對照

| 用途 | 元件 |
|------|------|
| 外殼 / 導覽 | `mat-sidenav`、`mat-toolbar` |
| 資料表 | `mat-table` + `mat-paginator` + `mat-sort` |
| 對話框 | `mat-dialog`（上傳、分析設定） |
| 分步表單 | `mat-stepper`（選配） |
| 進度 | `mat-progress-bar`、`mat-spinner` |
| 標記 | `mat-chip`（狀態、型別） |
| 分頁呈現 | `mat-tabs`（詳情頁、結果分區） |
| 表單 | `mat-form-field`、`mat-select`、`mat-checkbox` |
| 選單 / 切換 | `mat-menu`、`mat-button-toggle`（圖表控制） |
| 提示 | `mat-snackbar` |
| 展開面板 | `mat-expansion-panel`（驗證錯誤） |

---

## 6. 預設與範圍取捨（YAGNI）

- **主題**：MVP 只做 Light；dark 之後以 Material theming 加。
- **圖表微調**：只做輕量面板（軸 / 色 / 範圍 / 數值標籤 / 下載圖片），不做完整圖表產生器。
- **背景任務指示器**：toolbar badge 為選配；列表 `processing` chip 已覆蓋主要需求。
- **不做**：資料列預覽頁（後端無對應 endpoint）、帳號登入（呼應 plan.md #3 不做 auth）。

---

## 7. 對後端的相依

- 資料集列表頁需 `GET /api/v1/datasets`（已在 [plan.md §3.5](plan.md)）。
- 分析歷史列表與詳情頁歷史區塊需 `GET /api/v1/analysis/tasks`（可依 `dataset_id` 篩選，已補進 plan.md §3.5）。
- 其餘皆對應計畫既有 endpoint。

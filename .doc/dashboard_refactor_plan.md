# 數據分析流程重構計畫 (Dataset-centric Dashboard Flow)

這是一份針對將系統從「任務導向 (Task-centric)」重構為「資料集導向 (Dataset-centric)」的評估與實作計畫。

## 評估與可行性分析

這個改動是非常好且具備高可行性的。目前的系統架構已經將資料集 (Dataset) 與分析任務 (AnalysisTask) 解耦（一對多關係）。要達到類似 Jupyter Notebook 或是 Tableau Dashboard 的使用體驗，我們不需要大幅度修改資料庫結構，只需要：
1. **後端自動觸發**：在上傳資料集完成後，自動發送一個基礎的「敘述性統計與相關性分析 (descriptive_with_correlation)」任務。
2. **重構前端呈現方式**：將原本只顯示單一任務的 `AnalysisResultsPage`，重構成以資料集為核心的 `DatasetDashboardPage`。這個頁面會把該資料集底下的**所有分析任務**，轉換為一個個**區塊 (Sections/Blocks)** 由上而下排列。
3. **區塊的增刪**：讓使用者在 Dashboard 中可以新增區塊（發送新的分析任務）與刪除區塊（呼叫 DELETE API 刪除任務）。

---

## 實作計畫

### 第一階段：後端 API 擴充與自動化

1. **自動觸發基礎分析**
   - **目標**：上傳資料完成後，自動產生基礎圖表與統計。
   - **作法**：修改 `backend/app/services/dataset_service.py` 中的 `upload_dataset` 流程，在資料集狀態標記為 READY 之後，直接呼叫 `AnalysisService.run_analysis`，並傳入 `task_type="descriptive_with_correlation"`。

2. **新增刪除分析任務的 API**
   - **目標**：允許使用者移除不想要的分析區塊。
   - **作法**：在 `backend/app/routes/analysis.py` 實作 `DELETE /api/v1/analysis/tasks/{task_id}` 端點，並在 `AnalysisRepository` 加入對應的刪除邏輯。

---

### 第二階段：前端架構與路由重構

1. **新增 Dataset Dashboard 路由**
   - **目標**：新的主要分析頁面。
   - **作法**：在 `app.routes.ts` 新增路由：`{ path: 'datasets/:id/dashboard', component: DatasetDashboardPage }`。

2. **實作 Dataset Dashboard 頁面元件 (`DatasetDashboardPage`)**
   - **目標**：作為 Notebook 的外殼，負責載入並管理所有的分析區塊。
   - **作法**：
     - 進入頁面時，呼叫 `API` 取得 Dataset 資訊，以及其關聯的所有 `AnalysisTask` (可透過 `/api/v1/analysis/tasks?dataset_id={id}` 取得)。
     - 遍歷所有 tasks，將每個 task 透過子元件渲染為一個獨立的 Section。
     - 頁面最下方提供「新增分析區塊 (Add Section)」的按鈕與選單（可選擇時間序列、分組分析等），點擊後發送新任務，並將狀態設為 Loading 加入畫面。

3. **將現有的 AnalysisResultsPage 抽離為 Section 元件 (`AnalysisBlockComponent`)**
   - **目標**：讓單一分析結果可以被重複且多個實例並存在同一個畫面中。
   - **作法**：
     - 將 `AnalysisResultsPage` 降級為 `AnalysisBlockComponent`，接收 `taskId` 或 `task` 物件作為 `@Input()`。
     - 元件內建自己的重整與刪除按鈕（觸發 `DELETE` API 並向上 Emit Event 請 Dashboard 移除該區塊）。
     - 依照不同的 `task_type` 動態渲染圖表，沿用現有的 Chart Switcher。

---

### 第三階段：UI/UX 調整與收尾

1. **調整資料集列表 (Datasets Page) 流程**
   - **作法**：移除原本每列旁邊的「選擇分析類型」下拉選單。改為一個直接前往「分析 Dashboard」的按鈕。

2. **清理多餘的舊頁面**
   - **作法**：如果 Dashboard 成功取代了舊流程，可考慮將原本的 `AnalysisHistoryPage` 轉作純粹的系統稽核日誌，或直接移除，因為使用者可以直接從資料集進入 Dashboard 看到所有紀錄。

---

> [!IMPORTANT]
> **Open Questions (需要您的確認)**
> 
> 1. **自動觸發的範圍**：目前規劃在上傳完成後自動執行「綜合分析 (Descriptive + Correlation)」。這可能會在處理超大型資料集時花費一些時間（1-5分鐘），使用者進入 Dashboard 時該區塊會顯示為 Loading 狀態，這樣是否符合您的期待？
> 2. **舊分析結果的處理**：新的流程是以 Dataset 為中心，原本左側導覽列的「分析歷史 (Analysis History)」頁面是否還需要保留，還是可以將重心完全轉移到「資料集清單」上？

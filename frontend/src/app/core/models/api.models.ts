/**
 * 資料集基本資訊
 */
export interface Dataset {
  /** 資料集唯一識別碼 */
  id: number;
  /** 原始檔案名稱 */
  filename: string;
  /** 資料列數 */
  row_count: number;
  /** 資料欄數 */
  column_count: number;
  /** 處理狀態 (例如: READY, PROCESSING, FAILED) */
  status: string;
  /** 建立時間 (ISO 8601 格式字串) */
  created_at: string;
  /** 伺服器上的檔案儲存路徑 */
  file_path: string;
}

/**
 * 資料集欄位 Schema 資訊
 */
export interface DatasetColumn {
  /** 欄位唯一識別碼 */
  id: number;
  /** 關聯的資料集 ID */
  dataset_id: number;
  /** 欄位名稱 */
  column_name: string;
  /** 欄位資料型態 (例如: string, number, datetime) */
  data_type: string;
  /** 空值數量 */
  null_count: number;
  /** 唯一值數量 */
  unique_count: number;
}

/**
 * 資料集詳細資訊 (包含其所有欄位 Schema)
 */
export interface DatasetDetail extends Dataset {
  /** 該資料集包含的所有欄位列表 */
  columns: DatasetColumn[];
}

/**
 * 資料集列表的分頁回應
 */
export interface DatasetListResponse {
  /** 資料集陣列 */
  items: Dataset[];
  /** 資料集總筆數 */
  total: number;
  /** 目前頁碼 */
  page: number;
  /** 每頁筆數 */
  page_size: number;
}

/**
 * 執行分析任務的請求參數
 */
export interface AnalysisRunRequest {
  /** 欲分析的資料集 ID */
  dataset_id: number;
  /** 分析類型 (例如: descriptive, correlation, group_by, time_series) */
  task_type: string;
  /** 指定要分析的欄位名稱陣列 (選填) */
  target_columns?: string[];
}

/**
 * 分析任務基本資訊
 */
export interface AnalysisTask {
  /** 任務唯一識別碼 */
  id: number;
  /** 關聯的資料集 ID */
  dataset_id: number;
  /** 分析類型 */
  task_type: string;
  /** Celery 背景任務 ID (可能為空，若尚未派發或同步執行) */
  celery_task_id?: string;
  /** 任務狀態 (例如: PENDING, STARTED, COMPLETED, FAILED) */
  status: string;
  /** 錯誤訊息 (如果狀態為 FAILED) */
  error_message?: string;
  /** 建立時間 (ISO 8601 格式字串) */
  created_at: string;
  /** 任務開始時間 (ISO 8601 格式字串) */
  started_at?: string;
  /** 任務完成時間 (ISO 8601 格式字串) */
  completed_at?: string;
}

/**
 * 單項分析結果摘要
 */
export interface AnalysisResultSummary {
  /** 指標名稱或類別名稱 */
  metric_name: string;
  /** 指標數值 (若分析回傳單一數值) */
  metric_value: number;
}

/**
 * 分析任務詳細資訊 (包含分析結果列表)
 */
export interface AnalysisTaskDetail extends AnalysisTask {
  /** 該任務帶來的所有結果摘要 */
  results: AnalysisResultSummary[];
}

/**
 * 分析任務列表的分頁回應
 */
export interface AnalysisTaskListResponse {
  /** 分析任務陣列 */
  items: AnalysisTask[];
  /** 任務總筆數 */
  total: number;
  /** 目前頁碼 */
  page: number;
  /** 每頁筆數 */
  page_size: number;
}

/**
 * 任務執行時間趨勢
 */
export interface TaskExecutionTrend {
  /** 任務開始時間 */
  started_at: string;
  /** 任務執行耗時 (毫秒) */
  duration_ms: number;
}

/**
 * 資料集預覽的回傳模型
 */
export interface DatasetPreviewResponse {
  /** 欄位名稱列表 */
  columns: string[];
  /** 資料內容，將欄位名稱映射到值 */
  data: Record<string, any>[];
}

/**
 * 任務圖表資料結構 (由各 metric 構成的彈性物件)
 */
export type ChartData = Record<string, any>;

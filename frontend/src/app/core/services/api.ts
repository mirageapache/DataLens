import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  Dataset,
  DatasetDetail,
  DatasetListResponse,
  AnalysisRunRequest,
  AnalysisTask,
  AnalysisTaskListResponse,
  AnalysisResultSummary,
  TaskExecutionTrend
} from '../models/api.models';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  // --- Datasets API ---

  /**
   * 上傳資料集檔案 (CSV 或 Excel)
   * @param file 欲上傳的檔案
   */
  uploadDataset(file: File): Observable<Dataset> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<Dataset>(`${this.apiUrl}/datasets/upload`, formData);
  }

  /**
   * 取得資料集分頁列表
   * @param page 頁碼 (預設 1)
   * @param pageSize 每頁筆數 (預設 20)
   */
  getDatasets(page: number = 1, pageSize: number = 20): Observable<DatasetListResponse> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
    return this.http.get<DatasetListResponse>(`${this.apiUrl}/datasets`, { params });
  }

  /**
   * 根據 ID 取得單一資料集的詳細資訊 (包含欄位 Schema)
   * @param id 資料集 ID
   */
  getDataset(id: number): Observable<DatasetDetail> {
    return this.http.get<DatasetDetail>(`${this.apiUrl}/datasets/${id}`);
  }

  // --- Analysis API ---

  /**
   * 觸發新的分析任務 (非同步背景執行)
   * @param req 分析任務請求參數 (包含資料集ID與分析類型等)
   */
  runAnalysis(req: AnalysisRunRequest): Observable<AnalysisTask> {
    return this.http.post<AnalysisTask>(`${this.apiUrl}/analysis/run`, req);
  }

  /**
   * 取得分析任務的歷史列表 (支援依資料集 ID 篩選)
   * @param page 頁碼 (預設 1)
   * @param pageSize 每頁筆數 (預設 20)
   * @param datasetId 篩選特定資料集的任務 (選填)
   */
  getAnalysisTasks(page: number = 1, pageSize: number = 20, datasetId?: number): Observable<AnalysisTaskListResponse> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
    if (datasetId) {
      params = params.set('dataset_id', datasetId.toString());
    }
    return this.http.get<AnalysisTaskListResponse>(`${this.apiUrl}/analysis/tasks`, { params });
  }

  /**
   * 取得任務執行時間的趨勢資料
   * @param datasetId 篩選特定資料集 (選填)
   */
  getAnalysisTaskTrend(datasetId?: number): Observable<TaskExecutionTrend[]> {
    let params = new HttpParams();
    if (datasetId) {
      params = params.set('dataset_id', datasetId.toString());
    }
    return this.http.get<TaskExecutionTrend[]>(`${this.apiUrl}/analysis/tasks/trend`, { params });
  }

  /**
   * 取得單一分析任務的當前狀態
   * @param taskId 任務 ID
   */
  getAnalysisTask(taskId: number): Observable<AnalysisTask> {
    return this.http.get<AnalysisTask>(`${this.apiUrl}/analysis/tasks/${taskId}`);
  }

  /**
   * 取得已完成任務的分析結果摘要 (不含圖表巨量資料)
   * @param taskId 任務 ID
   */
  getAnalysisTaskResults(taskId: number): Observable<AnalysisResultSummary[]> {
    return this.http.get<AnalysisResultSummary[]>(`${this.apiUrl}/analysis/tasks/${taskId}/results`);
  }

  /**
   * 取得任務對應圖表所需的 JSON 結構化資料
   * @param taskId 任務 ID
   */
  getAnalysisTaskCharts(taskId: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/analysis/tasks/${taskId}/charts`);
  }
}

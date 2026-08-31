import { Component, Input, Output, EventEmitter, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api';
import { DatasetPreviewResponse, Dataset } from '../../../core/models/api.models';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-dataset-preview',
  imports: [CommonModule, FormsModule],
  templateUrl: './dataset-preview.html'
})
export class DatasetPreview implements OnInit {
  @Input() datasetItem!: Dataset;
  @Output() back = new EventEmitter<void>();
  @Output() deleteAction = new EventEmitter<number>();
  @Output() analyzeAction = new EventEmitter<number>();

  private api = inject(ApiService);

  isLoading = false;
  error: string | null = null;
  previewData: DatasetPreviewResponse | null = null;
  
  previewLimit = 100;
  limitOptions = [100, 200, 500, 800, 1200];
  isDropdownOpen = false;

  /**
   * 元件初始化時，自動載入預覽資料
   */
  ngOnInit() {
    this.loadPreview();
  }

  /**
   * 呼叫 API 取得特定資料集的預覽內容（限制筆數）
   */
  loadPreview() {
    if (!this.datasetItem || !this.datasetItem.id) return;
    
    this.isLoading = true;
    this.error = null;
    this.api.getDatasetPreview(this.datasetItem.id, this.previewLimit).subscribe({
      next: (res) => {
        this.previewData = res;
        this.isLoading = false;
      },
      error: (err) => {
        this.error = '無法載入資料集預覽內容';
        this.isLoading = false;
      }
    });
  }

  /**
   * 觸發返回事件，通知父元件關閉預覽畫面
   */
  onBack() {
    this.back.emit();
  }

  /**
   * 當使用者更改顯示筆數限制時，重新載入預覽資料
   */
  onLimitChange() {
    this.loadPreview();
  }

  /**
   * 根據當前環境設定的 API 網址，開啟新分頁下載實體資料集檔案
   */
  downloadDataset() {
    if (!this.datasetItem || !this.datasetItem.id) return;
    const url = `${environment.apiUrl}/datasets/${this.datasetItem.id}/download`;
    window.open(url, '_blank');
  }

  /**
   * 觸發刪除事件，交由父元件處理實際刪除邏輯
   */
  onDelete() {
    this.deleteAction.emit(this.datasetItem.id);
  }

  /**
   * 觸發分析事件，交由父元件處理導航
   */
  onAnalyze() {
    this.analyzeAction.emit(this.datasetItem.id);
  }

  /**
   * 切換下拉選單顯示狀態
   */
  toggleDropdown() {
    this.isDropdownOpen = !this.isDropdownOpen;
  }
}

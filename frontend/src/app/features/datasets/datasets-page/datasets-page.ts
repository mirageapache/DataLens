import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api';
import { Dataset } from '../../../core/models/api.models';

@Component({
  selector: 'app-datasets-page',
  imports: [CommonModule, FormsModule],
  templateUrl: './datasets-page.html',
  styleUrl: './datasets-page.css',
})
export class DatasetsPage implements OnInit {
  private api = inject(ApiService);

  datasets: Dataset[] = [];
  totalCount = 0;
  page = 1;
  pageSize = 10;
  isLoading = false;

  isUploadModalOpen = false;
  isDragging = false;
  selectedFile: File | null = null;
  isUploading = false;
  uploadError: string | null = null;

  toastMessage: string | null = null;
  toastType: 'success' | 'error' | 'info' = 'success';

  ngOnInit() {
    this.loadDatasets();
  }

  loadDatasets() {
    this.isLoading = true;
    this.api.getDatasets(this.page, this.pageSize).subscribe({
      next: (res) => {
        this.datasets = res.items;
        this.totalCount = res.total;
        this.isLoading = false;
      },
      error: (err) => {
        this.showToast('無法載入資料集列表', 'error');
        this.isLoading = false;
      }
    });
  }

  openUploadDialog() {
    this.isUploadModalOpen = true;
    this.selectedFile = null;
    this.uploadError = null;
  }

  closeUploadDialog() {
    this.isUploadModalOpen = false;
    this.selectedFile = null;
    this.uploadError = null;
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragging = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragging = false;
    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      this.handleFile(event.dataTransfer.files[0]);
    }
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.handleFile(input.files[0]);
    }
  }

  handleFile(file: File) {
    this.uploadError = null;
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'csv' && ext !== 'xlsx') {
      this.uploadError = '僅支援 .csv 或 .xlsx 格式檔案！';
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      this.uploadError = '檔案大小超過 50MB 上限！';
      return;
    }
    this.selectedFile = file;
  }

  removeSelectedFile() {
    this.selectedFile = null;
    this.uploadError = null;
  }

  submitUpload() {
    if (!this.selectedFile) return;
    this.isUploading = true;
    this.api.uploadDataset(this.selectedFile).subscribe({
      next: (res) => {
        this.isUploading = false;
        this.closeUploadDialog();
        this.showToast('檔案上傳與解析成功！', 'success');
        this.loadDatasets();
      },
      error: (err) => {
        this.isUploading = false;
        this.uploadError = err.error?.detail || '上傳失敗，請稍後再試。';
      }
    });
  }

  triggerAnalysis(datasetId: number) {
    this.api.runAnalysis({ dataset_id: datasetId, task_type: 'descriptive' }).subscribe({
      next: (task) => {
        this.showToast('分析任務已觸發！', 'success');
        // TODO: Navigate to analysis status page
      },
      error: (err) => {
        this.showToast('觸發分析失敗', 'error');
      }
    });
  }

  deleteDataset(datasetId: number) {
    if (confirm('確定要刪除這筆資料集嗎？此操作將無法復原。')) {
      this.api.deleteDataset(datasetId).subscribe({
        next: () => {
          this.showToast('資料集已成功刪除！', 'success');
          this.loadDatasets();
        },
        error: (err) => {
          this.showToast('刪除失敗，請稍後再試。', 'error');
        }
      });
    }
  }

  showToast(message: string, type: 'success' | 'error' | 'info' = 'success') {
    this.toastMessage = message;
    this.toastType = type;
    setTimeout(() => {
      this.toastMessage = null;
    }, 4000);
  }
}

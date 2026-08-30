import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule, ActivatedRoute } from '@angular/router';
import { ApiService } from '../../../core/services/api';
import { Dataset } from '../../../core/models/api.models';
import { DatasetPreview } from '../dataset-preview/dataset-preview';
import { HttpEvent, HttpEventType } from '@angular/common/http';

@Component({
  selector: 'app-datasets-page',
  imports: [CommonModule, FormsModule, RouterModule, DatasetPreview],
  templateUrl: './datasets-page.html',
})
export class DatasetsPage implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  datasets: Dataset[] = [];
  totalCount = 0;
  page = 1;
  pageSize = 10;
  isLoading = false;

  selectedDatasetId: number | null = null;
  selectedDatasetName: string = '';
  selectedDataset: Dataset | null = null;

  isUploadModalOpen = false;
  isDragging = false;
  selectedFile: File | null = null;
  isUploading = false;
  uploadProgress = 0;
  uploadError: string | null = null;

  toastMessage: string | null = null;
  toastType: 'success' | 'error' | 'info' = 'success';
  private toastTimer: any = null;

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

        const previewId = this.route.snapshot.queryParams['preview'];
        if (previewId) {
          const datasetToPreview = this.datasets.find(d => d.id === +previewId);
          if (datasetToPreview) {
            this.viewDataset(datasetToPreview);
          }
          this.router.navigate([], { queryParams: { preview: null }, queryParamsHandling: 'merge', replaceUrl: true });
        }
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
    this.uploadProgress = 0;
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
    if (ext !== 'csv' && ext !== 'xlsx' && ext !== 'xls') {
      this.uploadError = '僅支援 .csv, .xlsx 或 .xls 格式檔案！';
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
    this.uploadProgress = 0;
    this.api.uploadDataset(this.selectedFile).subscribe({
      next: (event: HttpEvent<Dataset>) => {
        if (event.type === HttpEventType.UploadProgress) {
          if (event.total) {
            this.uploadProgress = Math.round(100 * event.loaded / event.total);
          }
        } else if (event.type === HttpEventType.Response) {
          this.isUploading = false;
          this.closeUploadDialog();
          this.showToast('檔案上傳與處理成功！', 'success');
          this.loadDatasets();
        }
      },
      error: (err) => {
        this.isUploading = false;
        this.uploadError = err.error?.detail || '上傳失敗，請稍後再試。';
      }
    });
  }

  goToDashboard(datasetId: number) {
    this.router.navigate(['/datasets', datasetId, 'dashboard']);
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

  deleteDatasetAndClose(datasetId: number) {
    if (confirm('確定要刪除這筆資料集嗎？此操作將無法復原。')) {
      this.api.deleteDataset(datasetId).subscribe({
        next: () => {
          this.showToast('資料集已成功刪除！', 'success');
          this.closePreview();
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
    if (this.toastTimer) {
      clearTimeout(this.toastTimer);
    }
    this.toastTimer = setTimeout(() => {
      this.toastMessage = null;
    }, 4000);
  }

  viewDataset(dataset: Dataset) {
    if (dataset.status.toUpperCase() !== 'READY') {
      this.showToast('資料集尚未處理完成，無法預覽', 'info');
      return;
    }
    this.selectedDatasetId = dataset.id;
    this.selectedDatasetName = dataset.filename;
    this.selectedDataset = dataset;
  }

  closePreview() {
    this.selectedDatasetId = null;
    this.selectedDatasetName = '';
    this.selectedDataset = null;
  }
}

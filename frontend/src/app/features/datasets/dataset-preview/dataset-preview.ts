import { Component, Input, Output, EventEmitter, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api';
import { DatasetPreviewResponse, Dataset } from '../../../core/models/api.models';

@Component({
  selector: 'app-dataset-preview',
  imports: [CommonModule, FormsModule],
  templateUrl: './dataset-preview.html'
})
export class DatasetPreview implements OnInit {
  @Input() datasetItem!: Dataset;
  @Output() back = new EventEmitter<void>();
  @Output() deleteAction = new EventEmitter<number>();

  private api = inject(ApiService);

  isLoading = false;
  error: string | null = null;
  previewData: DatasetPreviewResponse | null = null;
  
  previewLimit = 100;
  limitOptions = [100, 200, 500, 800, 1200];

  ngOnInit() {
    this.loadPreview();
  }

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

  onBack() {
    this.back.emit();
  }

  onLimitChange() {
    this.loadPreview();
  }

  downloadDataset() {
    if (!this.datasetItem || !this.datasetItem.id) return;
    const url = `/api/v1/datasets/${this.datasetItem.id}/download`;
    window.open(url, '_blank');
  }

  onDelete() {
    this.deleteAction.emit(this.datasetItem.id);
  }
}

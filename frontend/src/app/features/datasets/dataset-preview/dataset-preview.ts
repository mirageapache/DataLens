import { Component, Input, Output, EventEmitter, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/services/api';
import { DatasetPreviewResponse } from '../../../core/models/api.models';

@Component({
  selector: 'app-dataset-preview',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dataset-preview.html',
  styleUrl: './dataset-preview.css'
})
export class DatasetPreview implements OnInit {
  @Input() datasetId!: number;
  @Input() datasetName: string = '資料集預覽';
  @Output() back = new EventEmitter<void>();

  private api = inject(ApiService);

  isLoading = false;
  error: string | null = null;
  previewData: DatasetPreviewResponse | null = null;

  ngOnInit() {
    this.loadPreview();
  }

  loadPreview() {
    if (!this.datasetId) return;
    
    this.isLoading = true;
    this.error = null;
    this.api.getDatasetPreview(this.datasetId, 100).subscribe({
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
}

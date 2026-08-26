import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { ApiService } from '../../../core/services/api';
import { AnalysisTask } from '../../../core/models/api.models';

@Component({
  selector: 'app-analysis-history-page',
  imports: [CommonModule, RouterModule],
  templateUrl: './analysis-history-page.html'
})
export class AnalysisHistoryPage implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);

  tasks: AnalysisTask[] = [];
  isLoading = false;
  page = 1;
  pageSize = 20;
  error: string | null = null;

  ngOnInit() {
    this.loadTasks();
  }

  loadTasks() {
    this.isLoading = true;
    this.error = null;
    this.api.getAnalysisTasks(this.page, this.pageSize).subscribe({
      next: (res) => {
        this.tasks = res.items;
        this.isLoading = false;
      },
      error: () => {
        this.error = '無法載入分析歷史紀錄，請確認伺服器連線後重試。';
        this.isLoading = false;
      }
    });
  }

  goToDashboard(taskId: number) {
    this.router.navigate(['/analysis', taskId, 'results']);
  }
}

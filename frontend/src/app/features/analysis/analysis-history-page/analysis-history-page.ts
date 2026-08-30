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

  getTaskTypeName(type: string): string {
    const map: Record<string, string> = {
      'descriptive': '敘述性統計',
      'correlation': '相關性分析',
      'descriptive_with_correlation': '敘述性統計與相關性',
      'group_by': '分組聚合分析',
      'time_series': '時間序列分析',
      'distribution': '數據分佈分析',
      'cross_tabulation': '交叉樞紐分析'
    };
    return map[type] || type;
  }
}

import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { ApiService } from '../../../core/services/api';
import { AnalysisTask } from '../../../core/models/api.models';

@Component({
  selector: 'app-analysis-history-page',
  standalone: true,
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

  ngOnInit() {
    this.loadTasks();
  }

  loadTasks() {
    this.isLoading = true;
    this.api.getAnalysisTasks(this.page, this.pageSize).subscribe({
      next: (res) => {
        this.tasks = res.items;
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      }
    });
  }

  goToDashboard(taskId: number) {
    this.router.navigate(['/analysis', taskId, 'results']);
  }
}

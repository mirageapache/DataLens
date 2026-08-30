import { Component, OnInit, inject } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute, RouterModule, Router } from '@angular/router';
import { AnalysisBlockComponent } from '../analysis-block/analysis-block.component';
import { ApiService } from '../../../core/services/api';

@Component({
  selector: 'app-analysis-results-page',
  standalone: true,
  imports: [CommonModule, RouterModule, AnalysisBlockComponent],
  templateUrl: './analysis-results-page.html'
})
export class AnalysisResultsPage implements OnInit {
  private route = inject(ActivatedRoute);
  public location = inject(Location);
  private router = inject(Router);
  private api = inject(ApiService);

  taskId!: number;

  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.taskId = +id;
      }
    });
  }

  deleteTask() {
    if (confirm('確定要刪除這筆分析報告嗎？')) {
      this.api.deleteAnalysisTask(this.taskId).subscribe({
        next: () => {
          this.location.back();
        },
        error: () => {
          alert('刪除失敗，請稍後再試。');
        }
      });
    }
  }
}

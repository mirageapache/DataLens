import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { Subject, timer, takeUntil, switchMap, catchError, of, filter } from 'rxjs';
import { ApiService } from '../../../core/services/api';
import { AnalysisTask } from '../../../core/models/api.models';

@Component({
  selector: 'app-analysis-status-page',
  imports: [CommonModule, RouterModule],
  templateUrl: './analysis-status-page.html'
})
export class AnalysisStatusPage implements OnInit, OnDestroy {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  private destroy$ = new Subject<void>();
  taskId!: number;
  task: AnalysisTask | null = null;
  error: string | null = null;

  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.taskId = +id;
        this.startPolling();
      }
    });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private startPolling() {
    // 立即觸發，之後每 2000ms 輪詢一次
    timer(0, 2000).pipe(
      takeUntil(this.destroy$),
      switchMap(() => this.api.getAnalysisTask(this.taskId).pipe(
        catchError(err => {
          this.error = '無法取得任務狀態，請確認伺服器連線。';
          return of(null);
        })
      )),
      filter((t): t is AnalysisTask => t !== null)
    ).subscribe(task => {
      this.task = task;
      const status = task.status.toUpperCase();
      
      if (status === 'COMPLETED') {
        // 任務成功，停止輪詢並跳轉到結果頁
        this.destroy$.next();
        setTimeout(() => {
          this.router.navigate(['/analysis', this.taskId, 'results']);
        }, 800); // 稍微延遲讓使用者看到成功狀態
      } else if (status === 'FAILED') {
        // 任務失敗，停止輪詢並顯示錯誤
        this.destroy$.next();
        this.error = task.error_message || '分析任務執行失敗。';
      }
    });
  }
}

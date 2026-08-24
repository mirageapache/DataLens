import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { Subject, takeUntil, catchError, expand, delay, EMPTY } from 'rxjs';
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
    let currentDelay = 2000;
    const maxDelay = 30000;

    this.api.getAnalysisTask(this.taskId).pipe(
      expand(task => {
        const status = task.status.toUpperCase();
        if (status === 'COMPLETED' || status === 'FAILED') {
          return EMPTY;
        }
        const delayTime = currentDelay;
        currentDelay = Math.min(currentDelay * 2, maxDelay);
        return this.api.getAnalysisTask(this.taskId).pipe(delay(delayTime));
      }),
      takeUntil(this.destroy$),
      catchError(err => {
        this.error = '無法取得任務狀態，請確認伺服器連線。';
        return EMPTY;
      })
    ).subscribe(task => {
      this.task = task;
      const status = task.status.toUpperCase();
      
      if (status === 'COMPLETED') {
        // 任務成功，停止輪詢並跳轉到結果頁 (expand 會自動結束)
        setTimeout(() => {
          this.router.navigate(['/analysis', this.taskId, 'results']);
        }, 800); // 稍微延遲讓使用者看到成功狀態
      } else if (status === 'FAILED') {
        // 任務失敗，停止輪詢並顯示錯誤
        this.error = task.error_message || '分析任務執行失敗。';
      }
    });
  }
}

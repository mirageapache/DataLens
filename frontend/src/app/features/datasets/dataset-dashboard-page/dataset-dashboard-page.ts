import { Component, OnInit, inject } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api';
import { DatasetDetail, AnalysisTask } from '../../../core/models/api.models';
import { AnalysisBlockComponent } from '../../analysis/analysis-block/analysis-block.component';

@Component({
  selector: 'app-dataset-dashboard-page',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, AnalysisBlockComponent],
  templateUrl: './dataset-dashboard-page.html'
})
export class DatasetDashboardPage implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);
  public location = inject(Location);

  datasetId!: number;
  dataset: DatasetDetail | null = null;
  tasks: AnalysisTask[] = [];
  
  isLoading = true;
  error: string | null = null;

  isCreatingNewTask = false;
  newTaskType = 'group_by';

  /**
   * 元件初始化時，訂閱路由參數取得資料集 ID，並載入儀表板資訊
   */
  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.datasetId = +id;
        this.loadDashboard();
      }
    });
  }

  /**
   * 載入資料集的詳細資訊與分析任務列表
   */
  loadDashboard() {
    this.isLoading = true;
    this.error = null;
    this.api.getDataset(this.datasetId).subscribe({
      next: (ds) => {
        this.dataset = ds;
        this.loadTasks();
      },
      error: () => {
        this.error = '無法載入資料集資訊。';
        this.isLoading = false;
      }
    });
  }

  /**
   * 呼叫 API 載入此資料集關聯的所有分析任務，並依建立時間降冪排序
   */
  loadTasks() {
    this.api.getAnalysisTasks(1, 100, this.datasetId).subscribe({
      next: (res) => {
        // Only show relevant tasks for this dataset
        this.tasks = res.items.filter(t => t.dataset_id === this.datasetId).sort((a, b) => {
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        });
        this.isLoading = false;
      },
      error: () => {
        this.error = '無法載入分析任務。';
        this.isLoading = false;
      }
    });
  }

  /**
   * 建立新的分析任務，成功後將其加到列表最前面
   */
  createNewTask() {
    this.isCreatingNewTask = true;
    this.api.runAnalysis({ dataset_id: this.datasetId, task_type: this.newTaskType }).subscribe({
      next: (task) => {
        this.tasks.unshift(task);
        this.isCreatingNewTask = false;
      },
      error: () => {
        alert('建立新分析區塊失敗');
        this.isCreatingNewTask = false;
      }
    });
  }

  /**
   * 當子元件(分析區塊)觸發刪除成功時，從目前的列表中移除該任務
   */
  onTaskDeleted(taskId: number) {
    this.tasks = this.tasks.filter(t => t.id !== taskId);
  }
}

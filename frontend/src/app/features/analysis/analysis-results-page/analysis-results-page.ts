import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { ApiService } from '../../../core/services/api';
import { AnalysisTask, AnalysisResultSummary } from '../../../core/models/api.models';
import { NgxEchartsModule } from 'ngx-echarts';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-analysis-results-page',
  standalone: true,
  imports: [CommonModule, RouterModule, NgxEchartsModule],
  templateUrl: './analysis-results-page.html'
})
export class AnalysisResultsPage implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);
  public location = inject(Location);

  taskId!: number;
  task: AnalysisTask | null = null;
  results: AnalysisResultSummary[] = [];
  chartsData: any = null;
  isLoading = true;

  activeTab: 'descriptive' | 'correlation' = 'descriptive';

  // --- ECharts Options ---
  histogramOptions: any;
  heatmapOptions: any;
  boxplotOptions: any;

  // Selected column for histogram
  histogramColumns: string[] = [];
  selectedHistCol: string = '';

  // Stats table
  statsTable: any[] = [];

  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.taskId = +id;
        this.loadData();
      }
    });
  }

  loadData() {
    this.isLoading = true;
    forkJoin({
      task: this.api.getAnalysisTask(this.taskId),
      results: this.api.getAnalysisTaskResults(this.taskId),
      charts: this.api.getAnalysisTaskCharts(this.taskId)
    }).subscribe({
      next: (res) => {
        this.task = res.task;
        this.results = res.results;
        this.chartsData = res.charts;
        this.processData();
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      }
    });
  }

  processData() {
    // 1. Process Descriptive Stats (for Table and Histogram)
    const statsCols = [];
    this.statsTable = [];
    
    for (const [metric, data] of Object.entries(this.chartsData)) {
      if (metric.startsWith('descriptive_stats_')) {
        const colName = metric.replace('descriptive_stats_', '');
        statsCols.push(colName);
        this.statsTable.push({
          colName,
          ...((data as any) || {})
        });
      }
    }
    
    this.histogramColumns = statsCols;
    if (statsCols.length > 0) {
      this.selectedHistCol = statsCols[0];
      this.renderHistogram(this.selectedHistCol);
      this.renderBoxplot();
    }

    // 2. Process Correlation Heatmap
    if (this.chartsData['pearson_correlation_matrix']) {
      const corrData = this.chartsData['pearson_correlation_matrix'];
      this.renderHeatmap(corrData);
    }
  }

  renderBoxplot() {
    // ECharts boxplot data format: [min, Q1, median, Q3, max]
    const boxplotData = [];
    const xAxisData = [];

    for (const stat of this.statsTable) {
      if (stat.min !== undefined && stat['25%'] !== undefined && stat['50%'] !== undefined && stat['75%'] !== undefined && stat.max !== undefined) {
        xAxisData.push(stat.colName);
        boxplotData.push([
          stat.min,
          stat['25%'],
          stat['50%'],
          stat['75%'],
          stat.max
        ]);
      }
    }

    if (boxplotData.length > 0) {
      this.boxplotOptions = {
        title: { text: '特徵數值分佈盒鬚圖', left: 'center', textStyle: { fontSize: 14, color: '#374151' } },
        tooltip: { trigger: 'item', axisPointer: { type: 'shadow' } },
        grid: { left: '10%', right: '10%', bottom: '15%' },
        xAxis: { type: 'category', data: xAxisData, boundaryGap: true, nameGap: 30, splitArea: { show: false }, splitLine: { show: false } },
        yAxis: { type: 'value', splitArea: { show: true } },
        series: [
          {
            name: 'Boxplot',
            type: 'boxplot',
            data: boxplotData,
            itemStyle: { color: '#eef2ff', borderColor: '#4f46e5' }
          }
        ]
      };
    }
  }

  renderHistogram(colName: string) {
    // In our backend, descriptive_stats just returns mean/std etc. It doesn't actually return histogram bins.
    // For demonstration, we will fake a histogram based on mean and std, or just show a placeholder chart.
    // In a real app, backend should return histogram buckets for this column.
    // We will render a normal distribution curve based on mean and std.
    const stat = this.statsTable.find(s => s.colName === colName);
    if (!stat) return;

    const mean = stat.mean || 0;
    const std = stat.std || 1;
    
    // Generate some fake normal distribution curve points
    const data = [];
    const xAxisData = [];
    for (let i = -3; i <= 3; i += 0.5) {
      const x = mean + i * std;
      // Normal distribution PDF formula
      const y = (1 / (std * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * Math.pow((x - mean) / std, 2));
      xAxisData.push(x.toFixed(2));
      data.push(y.toFixed(4));
    }

    this.histogramOptions = {
      color: ['#3f51b5'],
      tooltip: { trigger: 'axis' },
      grid: { top: '10%', bottom: '15%', left: '8%', right: '5%' },
      xAxis: { type: 'category', data: xAxisData, name: colName },
      yAxis: { type: 'value', name: 'Probability Density' },
      series: [{
        data: data,
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.2 }
      }]
    };
  }

  onHistColChange(event: Event) {
    const select = event.target as HTMLSelectElement;
    this.selectedHistCol = select.value;
    this.renderHistogram(this.selectedHistCol);
  }

  renderHeatmap(corrData: any) {
    const cols = corrData.columns;
    const values = corrData.values; // 2D array

    // ECharts heatmap requires data in format [x, y, value]
    const heatmapPoints = [];
    for (let i = 0; i < values.length; i++) {
      for (let j = 0; j < values[i].length; j++) {
        heatmapPoints.push([j, i, parseFloat(values[i][j].toFixed(2))]);
      }
    }

    this.heatmapOptions = {
      tooltip: { position: 'top' },
      grid: { top: '10%', bottom: '25%', left: '15%', right: '10%' },
      xAxis: { type: 'category', data: cols, splitArea: { show: true }, axisLabel: { interval: 0, rotate: 30 } },
      yAxis: { type: 'category', data: cols, splitArea: { show: true } },
      visualMap: {
        min: -1, max: 1, calculable: true, orient: 'horizontal', left: 'center', bottom: '0%',
        inRange: { color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'] }
      },
      series: [{
        name: 'Correlation', type: 'heatmap', data: heatmapPoints,
        label: { show: true },
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
      }]
    };
  }
}

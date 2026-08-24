import { Component, OnInit, inject } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { ApiService } from '../../../core/services/api';
import { AnalysisTask, AnalysisResultSummary } from '../../../core/models/api.models';
import { NgxEchartsModule } from 'ngx-echarts';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-analysis-results-page',
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
  error: string | null = null;

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
    this.error = null;
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
        this.error = '無法載入分析結果，請確認伺服器連線後重試。';
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
    const stat = this.statsTable.find(s => s.colName === colName);
    if (!stat) return;

    const bins = stat.histogram_bins;
    // 後端已回傳真實分桶資料，直接繪製柱狀圖
    if (bins && bins.labels?.length > 0) {
      this.histogramOptions = {
        color: ['#3f51b5'],
        tooltip: { trigger: 'axis', formatter: '{b}<br/>Count: {c}' },
        grid: { top: '10%', bottom: '20%', left: '10%', right: '5%' },
        xAxis: {
          type: 'category',
          data: bins.labels,
          name: colName,
          axisLabel: { rotate: 30, fontSize: 10 }
        },
        yAxis: { type: 'value', name: 'Count' },
        series: [{
          data: bins.counts,
          type: 'bar',
          barMaxWidth: 40,
          itemStyle: { color: '#3f51b5', opacity: 0.8 }
        }]
      };
    } else {
      // Fallback：後端無分桶資料，改顯示無資料提示
      this.histogramOptions = null;
    }
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

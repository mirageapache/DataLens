import { Component, OnInit, inject } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { ApiService } from '../../../core/services/api';
import { AnalysisTask, AnalysisResultSummary, ChartData } from '../../../core/models/api.models';
import { NgxEchartsModule } from 'ngx-echarts';
import { forkJoin } from 'rxjs';
import { ChartSwitcherComponent } from '../components/chart-switcher/chart-switcher.component';

@Component({
  selector: 'app-analysis-results-page',
  standalone: true,
  imports: [CommonModule, RouterModule, NgxEchartsModule, ChartSwitcherComponent],
  templateUrl: './analysis-results-page.html'
})
export class AnalysisResultsPage implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);
  public location = inject(Location);

  taskId!: number;
  task: AnalysisTask | null = null;
  results: AnalysisResultSummary[] = [];
  chartsData: ChartData = {};
  isLoading = true;
  error: string | null = null;

  activeTab: string = '';
  availableTabs: { id: string, label: string, icon: string }[] = [];

  // --- ECharts Options ---
  histogramOptions: any;
  heatmapOptions: any;
  boxplotOptions: any;
  
  // Generic charts (for group_by, time_series, cross_tabulation, distribution)
  genericChartOptions: any = null;
  genericAvailableCharts: string[] = [];
  genericActiveChart: string = '';
  genericMetricName: string = '';
  genericRawData: any = null;

  // Selected column for histogram
  histogramColumns: string[] = [];
  selectedHistCol: string = '';

  // Stats table
  statsTable: any[] = [];

  // Common ECharts features (Phase 4.4 enhancements)
  private getCommonToolbox() {
    return {
      feature: {
        dataZoom: { yAxisIndex: 'none', title: { zoom: '區域縮放', back: '還原縮放' } },
        dataView: { readOnly: false, title: '資料檢視' },
        magicType: { type: ['line', 'bar'], title: { line: '切換為折線圖', bar: '切換為長條圖' } },
        restore: { title: '還原' },
        saveAsImage: { title: '儲存為圖片' }
      }
    };
  }

  private getCommonDataZoom() {
    return [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', bottom: '2%', height: 25 }
    ];
  }

  private getCommonTooltip() {
    return { trigger: 'axis', axisPointer: { type: 'cross', crossStyle: { color: '#999' } } };
  }

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
  
  setupTabs() {
    this.availableTabs = [];
    if (!this.task) return;
    
    switch (this.task.task_type) {
      case 'descriptive':
        this.availableTabs.push({ id: 'descriptive', label: '描述性統計與分佈', icon: 'fa-calculator' });
        break;
      case 'correlation':
        this.availableTabs.push({ id: 'correlation', label: '相關性分析', icon: 'fa-border-all' });
        break;
      case 'descriptive_with_correlation':
        this.availableTabs.push({ id: 'descriptive', label: '描述性統計與分佈', icon: 'fa-calculator' });
        this.availableTabs.push({ id: 'correlation', label: '相關性分析', icon: 'fa-border-all' });
        break;
      case 'group_by':
        this.availableTabs.push({ id: 'group_by', label: '分組聚合分析', icon: 'fa-layer-group' });
        break;
      case 'time_series':
        this.availableTabs.push({ id: 'time_series', label: '時間序列趨勢', icon: 'fa-chart-line' });
        break;
      case 'distribution':
        this.availableTabs.push({ id: 'distribution', label: '分佈與異常值分析', icon: 'fa-boxes-stacked' });
        break;
      case 'cross_tabulation':
        this.availableTabs.push({ id: 'cross_tabulation', label: '類別交叉樞紐分析', icon: 'fa-table' });
        break;
    }
    
    if (this.availableTabs.length > 0) {
      this.activeTab = this.availableTabs[0].id;
    }
  }

  processData() {
    this.setupTabs();

    // 1. Process Descriptive Stats
    const statsCols = [];
    this.statsTable = [];
    
    for (const [metric, res] of Object.entries(this.chartsData)) {
      if (metric.startsWith('descriptive_stats_')) {
        const colName = metric.replace('descriptive_stats_', '');
        statsCols.push(colName);
        this.statsTable.push({
          colName,
          ...(res.chart_data || {})
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
      const res = this.chartsData['pearson_correlation_matrix'];
      this.renderHeatmap(res.chart_data);
    }
    
    // 3. Process Generic Charts
    this.processGenericCharts();
  }
  
  processGenericCharts() {
    if (!this.task) return;
    
    let targetMetric = '';
    for (const metric of Object.keys(this.chartsData)) {
      if (this.task.task_type === 'group_by' && metric.startsWith('group_by_')) targetMetric = metric;
      else if (this.task.task_type === 'time_series' && metric.startsWith('time_series_trend_')) targetMetric = metric;
      else if (this.task.task_type === 'cross_tabulation' && metric.startsWith('cross_tab_')) targetMetric = metric;
      else if (this.task.task_type === 'distribution' && metric.startsWith('distribution_boxplot_')) {
        targetMetric = metric;
        break;
      }
    }
    
    if (targetMetric && this.chartsData[targetMetric]) {
      this.genericMetricName = targetMetric;
      this.genericRawData = this.chartsData[targetMetric].chart_data;
      this.genericAvailableCharts = this.chartsData[targetMetric].recommended_charts || ['bar'];
      
      if (this.genericAvailableCharts.length > 0) {
        this.onGenericChartChange(this.genericAvailableCharts[0]);
      }
    }
  }

  onGenericChartChange(chartType: string) {
    this.genericActiveChart = chartType;
    if (!this.genericRawData) return;
    
    const data = this.genericRawData;
    
    if (chartType === 'bar' || chartType === 'stacked_bar') {
      const seriesNames = data.series_names || Object.keys(data.series);
      const isStacked = chartType === 'stacked_bar';
      
      this.genericChartOptions = {
        tooltip: this.getCommonTooltip(),
        toolbox: this.getCommonToolbox(),
        dataZoom: this.getCommonDataZoom(),
        legend: { data: seriesNames, top: 0 },
        grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
        xAxis: { type: 'category', data: data.categories || data.time_labels, axisLabel: { rotate: 30 } },
        yAxis: { type: 'value' },
        series: seriesNames.map((name: string) => ({
          name,
          type: 'bar',
          stack: isStacked ? 'total' : undefined,
          data: data.series[name],
          emphasis: { focus: 'series' }
        }))
      };
    } 
    else if (chartType === 'line' || chartType === 'area') {
      const seriesNames = data.series_names || Object.keys(data.series);
      const isArea = chartType === 'area';
      
      this.genericChartOptions = {
        tooltip: this.getCommonTooltip(),
        toolbox: this.getCommonToolbox(),
        dataZoom: this.getCommonDataZoom(),
        legend: { data: seriesNames, top: 0 },
        grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: data.time_labels || data.categories },
        yAxis: { type: 'value' },
        series: seriesNames.map((name: string) => ({
          name,
          type: 'line',
          areaStyle: isArea ? {} : undefined,
          smooth: true,
          data: data.series[name],
          emphasis: { focus: 'series' }
        }))
      };
    }
    else if (chartType === 'dual_axis') {
      const seriesNames = data.series_names || Object.keys(data.series);
      
      if (seriesNames.length < 2) {
        // Fallback to line if not enough series
        this.onGenericChartChange('line');
        return;
      }
      
      const leftSeries = seriesNames[0];
      const rightSeries = seriesNames[1];
      
      this.genericChartOptions = {
        tooltip: this.getCommonTooltip(),
        toolbox: this.getCommonToolbox(),
        dataZoom: this.getCommonDataZoom(),
        legend: { data: [leftSeries, rightSeries], top: 0 },
        grid: { left: '3%', right: '3%', bottom: '15%', top: '15%', containLabel: true },
        xAxis: { type: 'category', data: data.time_labels || data.categories, axisLabel: { rotate: 30 } },
        yAxis: [
          { type: 'value', name: leftSeries, position: 'left' },
          { type: 'value', name: rightSeries, position: 'right', splitLine: { show: false } }
        ],
        series: [
          {
            name: leftSeries,
            type: 'bar',
            yAxisIndex: 0,
            data: data.series[leftSeries],
            emphasis: { focus: 'series' }
          },
          {
            name: rightSeries,
            type: 'line',
            yAxisIndex: 1,
            smooth: true,
            data: data.series[rightSeries],
            emphasis: { focus: 'series' }
          }
        ]
      };
    }
    else if (chartType === 'pie' || chartType === 'donut') {
      const seriesNames = Object.keys(data.series);
      if (seriesNames.length === 0) return;
      
      const targetSeries = seriesNames[0];
      const pieData = (data.categories || []).map((cat: string, index: number) => ({
        name: cat,
        value: data.series[targetSeries][index]
      }));
      
      const isDonut = chartType === 'donut';
      
      this.genericChartOptions = {
        tooltip: { trigger: 'item', formatter: '{a} <br/>{b} : {c} ({d}%)' },
        toolbox: { feature: { saveAsImage: { title: '儲存為圖片' } } },
        legend: { type: 'scroll', orient: 'vertical', right: 10, top: 20, bottom: 20 },
        series: [
          {
            name: targetSeries,
            type: 'pie',
            radius: isDonut ? ['40%', '70%'] : '50%',
            center: ['40%', '50%'],
            data: pieData,
            emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
          }
        ]
      };
    }
    else if (chartType === 'boxplot') {
      const boxData = [[
        data.min, data.q1, data.median, data.q3, data.max
      ]];
      this.genericChartOptions = {
        title: { text: this.genericMetricName, left: 'center' },
        tooltip: { trigger: 'item', axisPointer: { type: 'shadow' } },
        toolbox: { feature: { saveAsImage: { title: '儲存為圖片' } } },
        grid: { left: '10%', right: '10%', bottom: '15%' },
        xAxis: { type: 'category', data: ['Data'], boundaryGap: true, splitArea: { show: false } },
        yAxis: { type: 'value', splitArea: { show: true } },
        series: [
          {
            name: 'Boxplot',
            type: 'boxplot',
            data: boxData,
            itemStyle: { color: '#eef2ff', borderColor: '#4f46e5' }
          }
        ]
      };
    }
    else if (chartType === 'heatmap') {
      if (data.categories && data.series_names) {
         const yAxis = data.categories;
         const xAxis = data.series_names;
         const heatmapPoints = [];
         let min = 0, max = 0;
         
         for (let i = 0; i < xAxis.length; i++) {
            const colData = data.series[xAxis[i]];
            for (let j = 0; j < yAxis.length; j++) {
               const val = colData[j] || 0;
               heatmapPoints.push([i, j, val]);
               if (val < min) min = val;
               if (val > max) max = val;
            }
         }
         
         this.genericChartOptions = {
          tooltip: { position: 'top' },
          toolbox: { feature: { saveAsImage: { title: '儲存為圖片' } } },
          grid: { top: '10%', bottom: '15%', left: '15%', right: '10%' },
          xAxis: { type: 'category', data: xAxis, splitArea: { show: true } },
          yAxis: { type: 'category', data: yAxis, splitArea: { show: true } },
          visualMap: {
            min: min, max: max, calculable: true, orient: 'horizontal', left: 'center', bottom: '0%'
          },
          series: [{
            name: 'Heatmap', type: 'heatmap', data: heatmapPoints,
            label: { show: true },
            emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
          }]
        };
      }
    }
  }

  renderBoxplot() {
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
        toolbox: { feature: { saveAsImage: { title: '儲存為圖片' } } },
        dataZoom: this.getCommonDataZoom(),
        grid: { left: '10%', right: '10%', bottom: '20%' },
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
    if (bins && bins.labels?.length > 0) {
      this.histogramOptions = {
        color: ['#3f51b5'],
        tooltip: this.getCommonTooltip(),
        toolbox: this.getCommonToolbox(),
        dataZoom: this.getCommonDataZoom(),
        grid: { top: '15%', bottom: '25%', left: '10%', right: '5%' },
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
    const values = corrData.values; 

    const heatmapPoints = [];
    for (let i = 0; i < values.length; i++) {
      for (let j = 0; j < values[i].length; j++) {
        heatmapPoints.push([j, i, parseFloat(values[i][j].toFixed(2))]);
      }
    }

    this.heatmapOptions = {
      tooltip: { position: 'top' },
      toolbox: { feature: { saveAsImage: { title: '儲存為圖片' } } },
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

import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

interface ChartConfig {
  id: string;
  label: string;
  icon: string;
}

@Component({
  selector: 'app-chart-switcher',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './chart-switcher.component.html'
})
export class ChartSwitcherComponent {
  @Input() availableCharts: string[] = [];
  @Input() activeChart: string = '';
  @Output() chartTypeChange = new EventEmitter<string>();

  // 定義支援的圖表類型與對應的 icon
  private chartConfigs: Record<string, ChartConfig> = {
    'bar': { id: 'bar', label: '長條圖', icon: 'fa-chart-column' },
    'histogram': { id: 'histogram', label: '直方圖', icon: 'fa-chart-bar' },
    'line': { id: 'line', label: '折線圖', icon: 'fa-chart-line' },
    'pie': { id: 'pie', label: '圓餅圖', icon: 'fa-chart-pie' },
    'donut': { id: 'donut', label: '環形圖', icon: 'fa-circle-notch' },
    'boxplot': { id: 'boxplot', label: '盒鬚圖', icon: 'fa-boxes-stacked' },
    'heatmap': { id: 'heatmap', label: '熱力圖', icon: 'fa-border-all' },
    'stacked_bar': { id: 'stacked_bar', label: '堆疊長條圖', icon: 'fa-align-left' },
    'area': { id: 'area', label: '面積圖', icon: 'fa-mountain' },
    'radar': { id: 'radar', label: '雷達圖', icon: 'fa-bullseye' },
  };

  get renderableCharts(): ChartConfig[] {
    return this.availableCharts
      .map(id => this.chartConfigs[id])
      .filter(config => config !== undefined);
  }

  onSelectChart(chartId: string) {
    if (this.activeChart !== chartId) {
      this.activeChart = chartId;
      this.chartTypeChange.emit(chartId);
    }
  }
}

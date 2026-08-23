import { Routes } from '@angular/router';
import { MainLayout } from './core/layout/main-layout/main-layout';
import { DatasetsPage } from './features/datasets/datasets-page/datasets-page';
import { AnalysisStatusPage } from './features/analysis/analysis-status-page/analysis-status-page';
import { AnalysisResultsPage } from './features/analysis/analysis-results-page/analysis-results-page';

export const routes: Routes = [
  {
    path: '',
    component: MainLayout,
    children: [
      { path: '', redirectTo: 'datasets', pathMatch: 'full' },
      { path: 'datasets', component: DatasetsPage },
      { path: 'analysis/:id/status', component: AnalysisStatusPage },
      { path: 'analysis/:id/results', component: AnalysisResultsPage }
    ]
  },
  { path: '**', redirectTo: '' }
];

import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ApiService } from './api';
import { environment } from '../../../environments/environment';
import { AnalysisRunRequest } from '../models/api.models';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;
  const apiUrl = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ApiService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    // 確保所有 HTTP 請求都已處理
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('Datasets API', () => {
    it('should upload a dataset correctly', () => {
      const mockFile = new File(['dummy content'], 'test.csv', { type: 'text/csv' });
      const mockResponse = { id: 1, filename: 'test.csv', size_bytes: 100, upload_date: '2023-01-01T00:00:00Z', status: 'READY' };

      service.uploadDataset(mockFile).subscribe(res => {
        expect(res).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${apiUrl}/datasets/upload`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body instanceof FormData).toBeTruthy();
      expect((req.request.body as FormData).get('file')).toBe(mockFile);
      req.flush(mockResponse);
    });

    it('should fetch datasets with pagination', () => {
      const mockResponse = { items: [], total: 0, page: 2, page_size: 10 };

      service.getDatasets(2, 10).subscribe(res => {
        expect(res).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(req => req.url === `${apiUrl}/datasets`);
      expect(req.request.method).toBe('GET');
      expect(req.request.params.get('page')).toBe('2');
      expect(req.request.params.get('page_size')).toBe('10');
      req.flush(mockResponse);
    });

    it('should delete dataset', () => {
      service.deleteDataset(1).subscribe();

      const req = httpMock.expectOne(`${apiUrl}/datasets/1`);
      expect(req.request.method).toBe('DELETE');
      req.flush(null);
    });
  });

  describe('Analysis API', () => {
    it('should run analysis', () => {
      const mockReq: AnalysisRunRequest = { dataset_id: 1, task_type: 'descriptive' };
      const mockResponse = { id: 10, dataset_id: 1, task_type: 'descriptive', status: 'PENDING' };

      service.runAnalysis(mockReq).subscribe(res => {
        expect(res).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${apiUrl}/analysis/run`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(mockReq);
      req.flush(mockResponse);
    });

    it('should fetch analysis tasks with optional datasetId', () => {
      const mockResponse = { items: [], total: 0, page: 1, page_size: 20 };

      service.getAnalysisTasks(1, 20, 5).subscribe(res => {
        expect(res).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(req => req.url === `${apiUrl}/analysis/tasks`);
      expect(req.request.method).toBe('GET');
      expect(req.request.params.get('page')).toBe('1');
      expect(req.request.params.get('page_size')).toBe('20');
      expect(req.request.params.get('dataset_id')).toBe('5');
      req.flush(mockResponse);
    });

    it('should get analysis task status', () => {
      const mockResponse = { id: 10, dataset_id: 1, task_type: 'descriptive', status: 'COMPLETED' };

      service.getAnalysisTask(10).subscribe(res => {
        expect(res).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${apiUrl}/analysis/tasks/10`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
    
    it('should fetch analysis task charts', () => {
      const mockResponse = { "metric_name": { recommended_charts: ['bar'], chart_data: {} } };

      service.getAnalysisTaskCharts(10).subscribe(res => {
        expect(res).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${apiUrl}/analysis/tasks/10/charts`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });
});

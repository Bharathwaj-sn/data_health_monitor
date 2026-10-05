import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { APPLICATION_CONFIG } from '../config/application-config';
import { ApiClient } from './api-client';
import { ApiError } from './api-error';
import { apiErrorInterceptor } from './api-error.interceptor';

describe('ApiClient', () => {
  let api: ApiClient;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([apiErrorInterceptor])),
        provideHttpClientTesting(),
        { provide: APPLICATION_CONFIG, useValue: { apiBasePath: '/api/v1' } }
      ]
    });
    api = TestBed.inject(ApiClient);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpTesting.verify());

  it('builds API URLs and typed query parameters centrally', () => {
    api.get<{ ready: boolean }>('/objects', {
      params: {
        catalog: 'main',
        limit: 25,
        includeVolumes: false,
        tags: ['certified', 'finance'],
        omitted: null
      }
    }).subscribe(response => expect(response.ready).toBe(true));

    const request = httpTesting.expectOne(candidate => candidate.url === '/api/v1/objects');
    expect(request.request.method).toBe('GET');
    expect(request.request.params.get('catalog')).toBe('main');
    expect(request.request.params.get('limit')).toBe('25');
    expect(request.request.params.get('includeVolumes')).toBe('false');
    expect(request.request.params.getAll('tags')).toEqual(['certified', 'finance']);
    expect(request.request.params.has('omitted')).toBe(false);
    request.flush({ ready: true });
  });

  it('normalizes backend failures into ApiError', () => {
    let receivedError: unknown;
    api.get('/unavailable').subscribe({ error: error => receivedError = error });

    const request = httpTesting.expectOne('/api/v1/unavailable');
    request.flush({ detail: 'Warehouse is unavailable.' }, {
      status: 503,
      statusText: 'Service Unavailable'
    });

    expect(receivedError).toBeInstanceOf(ApiError);
    expect(receivedError).toMatchObject({
      message: 'Warehouse is unavailable.',
      status: 503,
      path: '/api/v1/unavailable'
    });
  });
});
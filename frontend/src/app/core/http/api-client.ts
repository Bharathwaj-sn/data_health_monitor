import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { APPLICATION_CONFIG } from '../config/application-config';

type QueryPrimitive = string | number | boolean;
type QueryValue = QueryPrimitive | readonly QueryPrimitive[];

export interface ApiRequestOptions {
  readonly headers?: Readonly<Record<string, string>>;
  readonly params?: Readonly<Record<string, QueryValue | null | undefined>>;
}

@Injectable({ providedIn: 'root' })
export class ApiClient {
  private readonly http = inject(HttpClient);
  private readonly configuration = inject(APPLICATION_CONFIG);

  get<Response>(path: string, options?: ApiRequestOptions): Observable<Response> {
    return this.http.get<Response>(this.url(path), this.options(options));
  }

  post<Response, Body = unknown>(path: string, body: Body, options?: ApiRequestOptions): Observable<Response> {
    return this.http.post<Response>(this.url(path), body, this.options(options));
  }

  put<Response, Body = unknown>(path: string, body: Body, options?: ApiRequestOptions): Observable<Response> {
    return this.http.put<Response>(this.url(path), body, this.options(options));
  }

  patch<Response, Body = unknown>(path: string, body: Body, options?: ApiRequestOptions): Observable<Response> {
    return this.http.patch<Response>(this.url(path), body, this.options(options));
  }

  delete<Response>(path: string, options?: ApiRequestOptions): Observable<Response> {
    return this.http.delete<Response>(this.url(path), this.options(options));
  }

  private url(path: string): string {
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${this.configuration.apiBasePath}${normalizedPath}`;
  }

  private options(options?: ApiRequestOptions): { headers: HttpHeaders; params: HttpParams } {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(options?.params ?? {})) {
      if (value === null || value === undefined) {
        continue;
      }
      const values = Array.isArray(value) ? value : [value];
      for (const item of values) {
        params = params.append(key, String(item));
      }
    }

    return {
      headers: new HttpHeaders(options?.headers ?? {}),
      params
    };
  }
}
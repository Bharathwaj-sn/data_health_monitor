import { HttpErrorResponse } from '@angular/common/http';

interface ApiErrorBody {
  readonly detail?: unknown;
}

export class ApiError extends Error {
  readonly status: number;
  readonly path: string;

  constructor(message: string, status: number, path: string, options?: ErrorOptions) {
    super(message, options);
    this.name = 'ApiError';
    this.status = status;
    this.path = path;
  }

  static fromHttpError(error: HttpErrorResponse, path: string): ApiError {
    const body = error.error as ApiErrorBody | string | null;
    const detail = typeof body === 'object' && body !== null ? body.detail : body;
    const message = typeof detail === 'string' && detail.trim()
      ? detail
      : error.status === 0
        ? 'The API is unavailable.'
        : 'The request could not be completed.';

    return new ApiError(message, error.status, path, { cause: error });
  }
}
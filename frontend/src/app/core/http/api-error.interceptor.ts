import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

import { ApiError } from './api-error';

export const apiErrorInterceptor: HttpInterceptorFn = (request, next) => next(request).pipe(
  catchError((error: unknown) => {
    const normalizedError = error instanceof HttpErrorResponse
      ? ApiError.fromHttpError(error, request.url)
      : error;
    return throwError(() => normalizedError);
  })
);
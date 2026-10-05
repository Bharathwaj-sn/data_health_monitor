import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { provideRouter } from '@angular/router';

import { environment } from '../environments/environment';
import { APPLICATION_CONFIG } from './core/config/application-config';
import { apiErrorInterceptor } from './core/http/api-error.interceptor';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideHttpClient(withFetch(), withInterceptors([apiErrorInterceptor])),
    provideRouter(routes),
    { provide: APPLICATION_CONFIG, useValue: environment }
  ]
};

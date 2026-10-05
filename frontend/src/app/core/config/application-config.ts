import { InjectionToken } from '@angular/core';

export interface ApplicationConfiguration {
  readonly apiBasePath: string;
}

export const APPLICATION_CONFIG = new InjectionToken<ApplicationConfiguration>('APPLICATION_CONFIG');
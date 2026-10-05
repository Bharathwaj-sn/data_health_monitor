import { computed, inject, Injectable, signal } from '@angular/core';

import { ApiError } from '../../../core/http/api-error';
import { DashboardApi, DatabricksIdentity, MetadataSummary } from './dashboard-api';

export type LoadState<T> =
  | { readonly status: 'loading' }
  | { readonly status: 'success'; readonly data: T }
  | { readonly status: 'empty' }
  | { readonly status: 'error'; readonly message: string };

@Injectable({ providedIn: 'root' })
export class DashboardStore {
  private readonly api = inject(DashboardApi);

  readonly identity = signal<LoadState<DatabricksIdentity>>({ status: 'loading' });
  readonly metadata = signal<LoadState<MetadataSummary>>({ status: 'loading' });
  readonly identityData = computed(() => {
    const state = this.identity();
    return state.status === 'success' ? state.data : null;
  });
  readonly identityError = computed(() => {
    const state = this.identity();
    return state.status === 'error' ? state.message : null;
  });
  readonly metadataData = computed(() => {
    const state = this.metadata();
    return state.status === 'success' ? state.data : null;
  });
  readonly metadataError = computed(() => {
    const state = this.metadata();
    return state.status === 'error' ? state.message : null;
  });

  readonly metadataAge = computed(() => {
    const state = this.metadata();
    return state.status === 'success'
      ? this.relativeTime(state.data.last_refreshed_at)
      : null;
  });

  constructor() {
    this.loadIdentity();
    this.loadMetadata();
  }

  reloadIdentity(): void {
    this.loadIdentity();
  }

  reloadMetadata(): void {
    this.loadMetadata();
  }

  private loadIdentity(): void {
    this.identity.set({ status: 'loading' });
    this.api.getDatabricksIdentity().subscribe({
      next: identity => this.identity.set({ status: 'success', data: identity }),
      error: (error: unknown) => this.identity.set({
        status: 'error',
        message: this.message(error, 'Databricks connection could not be verified.')
      })
    });
  }

  private loadMetadata(): void {
    this.metadata.set({ status: 'loading' });
    this.api.getMetadataSummary().subscribe({
      next: metadata => this.metadata.set(metadata.last_refreshed_at
        ? { status: 'success', data: metadata }
        : { status: 'empty' }),
      error: (error: unknown) => this.metadata.set(error instanceof ApiError && error.status === 404
        ? { status: 'empty' }
        : { status: 'error', message: this.message(error, 'Metadata status is unavailable.') })
    });
  }

  private message(error: unknown, fallback: string): string {
    return error instanceof Error && error.message ? error.message : fallback;
  }

  private relativeTime(value: string | null): string | null {
    if (!value) {
      return null;
    }
    const differenceSeconds = Math.round((new Date(value).getTime() - Date.now()) / 1000);
    const absoluteSeconds = Math.abs(differenceSeconds);
    const formatter = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
    if (absoluteSeconds < 60) {
      return formatter.format(differenceSeconds, 'second');
    }
    if (absoluteSeconds < 3600) {
      return formatter.format(Math.round(differenceSeconds / 60), 'minute');
    }
    if (absoluteSeconds < 86400) {
      return formatter.format(Math.round(differenceSeconds / 3600), 'hour');
    }
    return formatter.format(Math.round(differenceSeconds / 86400), 'day');
  }
}
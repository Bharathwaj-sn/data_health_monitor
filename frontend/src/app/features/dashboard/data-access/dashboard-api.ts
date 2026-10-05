import { inject, Injectable } from '@angular/core';

import { ApiClient } from '../../../core/http/api-client';

export interface DatabricksEmail {
  readonly value?: string;
  readonly primary?: boolean;
}

export interface DatabricksIdentity {
  readonly authenticated: boolean;
  readonly user_name: string | null;
  readonly emails: readonly DatabricksEmail[] | null;
}

export interface MetadataSummary {
  readonly catalog_count: number;
  readonly schema_count: number;
  readonly table_count: number;
  readonly volume_count: number;
  readonly last_refreshed_at: string | null;
  readonly status: string;
  readonly scope_type: string | null;
  readonly catalog_name: string | null;
  readonly schema_name: string | null;
}

export interface GenieSpaceStatus {
  readonly space_id: string | null;
  readonly title: string | null;
  readonly status: string;
}

@Injectable({ providedIn: 'root' })
export class DashboardApi {
  private readonly api = inject(ApiClient);

  getDatabricksIdentity() {
    return this.api.get<DatabricksIdentity>('/databricks/whoami');
  }

  getMetadataSummary() {
    return this.api.get<MetadataSummary>('/metadata/summary');
  }

  getGenieSpaceStatus() {
    return this.api.get<GenieSpaceStatus>('/genie-space/status');
  }
}
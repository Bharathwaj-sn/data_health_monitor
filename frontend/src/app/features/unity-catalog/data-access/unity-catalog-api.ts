import { inject, Injectable } from '@angular/core';

import { ApiClient } from '../../../core/http/api-client';

export interface NamedCatalogObject {
  readonly name: string;
}

export interface CatalogsResponse {
  readonly catalogs: readonly NamedCatalogObject[];
}

export interface SchemasResponse {
  readonly schemas: readonly NamedCatalogObject[];
}

export interface SchemaObjectsResponse {
  readonly tables: readonly NamedCatalogObject[];
  readonly volumes: readonly NamedCatalogObject[];
}

@Injectable({ providedIn: 'root' })
export class UnityCatalogApi {
  private readonly api = inject(ApiClient);

  getCatalogs() {
    return this.api.get<CatalogsResponse>('/databricks/catalogs');
  }

  getSchemas(catalogName: string) {
    return this.api.post<SchemasResponse>('/databricks/schemas:lookup', {
      catalog_name: catalogName
    });
  }

  getSchemaObjects(catalogName: string, schemaName: string) {
    return this.api.post<SchemaObjectsResponse>('/databricks/schema-objects:lookup', {
      catalog_name: catalogName,
      schema_name: schemaName
    });
  }
}
import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatTreeModule } from '@angular/material/tree';
import {
  LucideChevronDown,
  LucideChevronRight,
  LucideCircleAlert,
  LucideDatabase,
  LucideFolder,
  LucideHardDrive,
  LucideRefreshCw,
  LucideTable2
} from '@lucide/angular';
import { BehaviorSubject, Observable } from 'rxjs';

import {
  SchemaObjectsResponse,
  SchemasResponse,
  UnityCatalogApi
} from './data-access/unity-catalog-api';

type CatalogNodeKind = 'catalog' | 'schema' | 'table' | 'volume' | 'empty' | 'error';
type NodeLoadState = 'idle' | 'loading' | 'loaded' | 'error';
type RootLoadState = 'loading' | 'loaded' | 'empty' | 'error';

interface CatalogNode {
  readonly id: string;
  readonly label: string;
  readonly kind: CatalogNodeKind;
  readonly catalogName?: string;
  readonly schemaName?: string;
  readonly retryParentId?: string;
  readonly expandable: boolean;
  readonly childrenChange?: BehaviorSubject<CatalogNode[]>;
  loadState: NodeLoadState;
  children?: CatalogNode[];
}

@Component({
  selector: 'app-unity-catalog-tree',
  imports: [
    MatButtonModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    MatTreeModule,
    LucideChevronDown,
    LucideChevronRight,
    LucideCircleAlert,
    LucideDatabase,
    LucideFolder,
    LucideHardDrive,
    LucideRefreshCw,
    LucideTable2
  ],
  templateUrl: './unity-catalog-tree.html',
  styleUrl: './unity-catalog-tree.sass'
})
export class UnityCatalogTree {
  private readonly api = inject(UnityCatalogApi);
  private readonly destroyRef = inject(DestroyRef);

  readonly nodes = signal<CatalogNode[]>([]);
  readonly rootState = signal<RootLoadState>('loading');
  readonly rootError = signal<string | null>(null);
  readonly childrenAccessor = (node: CatalogNode) => node.childrenChange ?? node.children ?? [];
  readonly expansionKey = (node: CatalogNode) => node.id;
  readonly trackBy = (_index: number, node: CatalogNode) => node.id;
  readonly isExpandable = (_index: number, node: CatalogNode) => node.expandable;

  constructor() {
    this.loadCatalogs();
  }

  loadCatalogs(): void {
    this.rootState.set('loading');
    this.rootError.set(null);
    this.api.getCatalogs().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: response => {
        const catalogs = [...response.catalogs]
          .sort((left, right) => left.name.localeCompare(right.name))
          .map(catalog => this.catalogNode(catalog.name));
        this.nodes.set(catalogs);
        this.rootState.set(catalogs.length ? 'loaded' : 'empty');
      },
      error: (error: unknown) => {
        this.nodes.set([]);
        this.rootError.set(this.errorMessage(error, 'Unity Catalog could not be loaded.'));
        this.rootState.set('error');
      }
    });
  }

  onExpanded(node: CatalogNode, expanded: boolean): void {
    if (expanded && node.loadState === 'idle') {
      this.loadChildren(node);
    }
  }

  retry(node: CatalogNode): void {
    if (!node.retryParentId) {
      return;
    }
    const parent = this.findNode(this.nodes(), node.retryParentId);
    if (parent) {
      this.loadChildren(parent);
    }
  }

  private loadChildren(node: CatalogNode): void {
    node.loadState = 'loading';
    this.setChildren(node, [this.statusNode(`${node.id}:loading`, 'Loading…', 'empty')]);

    const request: Observable<SchemasResponse | SchemaObjectsResponse> = node.kind === 'catalog'
      ? this.api.getSchemas(node.catalogName!)
      : this.api.getSchemaObjects(node.catalogName!, node.schemaName!);

    request.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: response => {
        if ('schemas' in response) {
          this.setChildren(node, [...response.schemas]
            .sort((left, right) => left.name.localeCompare(right.name))
            .map(schema => this.schemaNode(node.catalogName!, schema.name)));
        } else {
          const tables = response.tables.map(table => this.objectNode(
            node.catalogName!,
            node.schemaName!,
            table.name,
            'table'
          ));
          const volumes = response.volumes.map(volume => this.objectNode(
            node.catalogName!,
            node.schemaName!,
            volume.name,
            'volume'
          ));
          this.setChildren(
            node,
            [...tables, ...volumes].sort((left, right) => left.label.localeCompare(right.label))
          );
        }
        node.loadState = 'loaded';
        if (!node.children?.length) {
          this.setChildren(node, [this.statusNode(`${node.id}:empty`, 'No objects found', 'empty')]);
        }
        this.touchNodes();
      },
      error: (error: unknown) => {
        node.loadState = 'error';
        this.setChildren(node, [{
          ...this.statusNode(`${node.id}:error`, this.errorMessage(error, 'Could not load this level.'), 'error'),
          retryParentId: node.id
        }]);
        this.touchNodes();
      }
    });
  }

  private catalogNode(name: string): CatalogNode {
    return {
      id: `catalog:${name}`,
      label: name,
      kind: 'catalog',
      catalogName: name,
      expandable: true,
      childrenChange: new BehaviorSubject<CatalogNode[]>([]),
      loadState: 'idle'
    };
  }

  private schemaNode(catalogName: string, schemaName: string): CatalogNode {
    return {
      id: `schema:${catalogName}.${schemaName}`,
      label: schemaName,
      kind: 'schema',
      catalogName,
      schemaName,
      expandable: true,
      childrenChange: new BehaviorSubject<CatalogNode[]>([]),
      loadState: 'idle'
    };
  }

  private objectNode(
    catalogName: string,
    schemaName: string,
    name: string,
    kind: 'table' | 'volume'
  ): CatalogNode {
    return {
      id: `${kind}:${catalogName}.${schemaName}.${name}`,
      label: name,
      kind,
      catalogName,
      schemaName,
      expandable: false,
      loadState: 'loaded'
    };
  }

  private statusNode(id: string, label: string, kind: 'empty' | 'error'): CatalogNode {
    return { id, label, kind, expandable: false, loadState: 'loaded' };
  }

  private findNode(nodes: CatalogNode[], id: string): CatalogNode | null {
    for (const node of nodes) {
      if (node.id === id) {
        return node;
      }
      const child = this.findNode(node.children ?? [], id);
      if (child) {
        return child;
      }
    }
    return null;
  }

  private touchNodes(): void {
    this.nodes.update(nodes => [...nodes]);
  }

  private setChildren(node: CatalogNode, children: CatalogNode[]): void {
    node.children = children;
    node.childrenChange?.next(children);
  }

  private errorMessage(error: unknown, fallback: string): string {
    return error instanceof Error && error.message ? error.message : fallback;
  }
}
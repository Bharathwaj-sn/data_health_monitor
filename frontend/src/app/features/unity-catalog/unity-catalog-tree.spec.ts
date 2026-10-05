import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { UnityCatalogApi } from './data-access/unity-catalog-api';
import { UnityCatalogTree } from './unity-catalog-tree';

describe('UnityCatalogTree', () => {
  const api = {
    getCatalogs: vi.fn(),
    getSchemas: vi.fn(),
    getSchemaObjects: vi.fn()
  };

  beforeEach(() => {
    vi.resetAllMocks();
    api.getCatalogs.mockReturnValue(of({ catalogs: [{ name: 'main' }] }));
    api.getSchemas.mockReturnValue(of({ schemas: [{ name: 'analytics' }] }));
    api.getSchemaObjects.mockReturnValue(of({
      tables: [{ name: 'claims' }],
      volumes: [{ name: 'exports' }]
    }));

    TestBed.configureTestingModule({
      imports: [UnityCatalogTree],
      providers: [{ provide: UnityCatalogApi, useValue: api }]
    });
  });

  it('defers child requests until each node is expanded', () => {
    const component = TestBed.createComponent(UnityCatalogTree).componentInstance;
    const catalog = component.nodes()[0];

    expect(api.getCatalogs).toHaveBeenCalledOnce();
    expect(api.getSchemas).not.toHaveBeenCalled();
    expect(component.rootState()).toBe('loaded');

    component.onExpanded(catalog, true);
    const schema = catalog.children![0];
    expect(api.getSchemas).toHaveBeenCalledWith('main');
    expect(api.getSchemaObjects).not.toHaveBeenCalled();

    component.onExpanded(schema, true);
    expect(api.getSchemaObjects).toHaveBeenCalledWith('main', 'analytics');
    expect(schema.children?.map(node => node.label)).toEqual(['claims', 'exports']);
  });

  it('retries a failed expanded level', () => {
    api.getSchemas
      .mockReturnValueOnce(throwError(() => new Error('Schemas are unavailable.')))
      .mockReturnValueOnce(of({ schemas: [{ name: 'recovered' }] }));
    const component = TestBed.createComponent(UnityCatalogTree).componentInstance;
    const catalog = component.nodes()[0];

    component.onExpanded(catalog, true);
    const errorNode = catalog.children![0];
    expect(errorNode.kind).toBe('error');
    expect(errorNode.label).toBe('Schemas are unavailable.');

    component.retry(errorNode);
    expect(api.getSchemas).toHaveBeenCalledTimes(2);
    expect(catalog.children?.[0].label).toBe('recovered');
  });
});
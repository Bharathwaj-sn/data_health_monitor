# Angular Frontend

## Scope today

The Angular application is a standalone Angular 21 SPA. Its implemented user
surface is deliberately narrow:

- A responsive application shell with navigation and a refresh action.
- A dashboard showing Databricks identity and metadata summary state.
- A lazy-loading Unity Catalog tree that browses live catalog, schema, table,
  and volume names.

The test-case, Genie generation, SQL saving, and execution workflow is not yet
implemented in Angular. It remains available through the legacy Streamlit
client described in [Legacy Streamlit client](legacy-streamlit.md).

## Bootstrap and routing

`src/main.ts` bootstraps `App` with `appConfig`. The app configuration provides
the Angular router, `HttpClient` using fetch, and an HTTP error interceptor.
The environment's `apiBasePath` is `/api/v1`.

The router has one shell route. `/` and all unknown routes redirect to
`/dashboard`; `/dashboard` lazy-loads `DashboardPage`. The shell adapts the
Material side navigation at handset, compact, and large breakpoints.

## Data access and state

`ApiClient` prepends `/api/v1` and supports typed `GET`, `POST`, `PUT`, `PATCH`,
and `DELETE` calls. The interceptor turns `HttpErrorResponse` values into the
project `ApiError` shape with status and request path. A status of zero is
presented as an unavailable API.

`DashboardStore` uses Angular signals for two independent states:

| State | Endpoint | Interpretation |
| --- | --- | --- |
| Databricks identity | `GET /databricks/whoami` | Confirms SDK-backed identity. |
| Metadata summary | `GET /metadata/summary` | Shows counts and last-refresh age; `404` is an empty pre-refresh state. |

Both states load when the store is constructed and reload from the dashboard's
refresh action. The state is in memory only.

## Unity Catalog browser

`UnityCatalogTree` loads root catalogs on construction. Expanding a catalog
loads schemas; expanding a schema loads tables and volumes. It sorts each level
alphabetically and tracks independent loading/error state at every expandable
node. Error nodes provide a retry action for their parent load.

The browser uses these live endpoints:

- `GET /databricks/catalogs`
- `POST /databricks/schemas:lookup`
- `POST /databricks/schema-objects:lookup`

This browser reads Databricks directly through FastAPI and does not change the
local metadata snapshot.

## Build and development proxy

The build uses SASS, Angular Material, Lucide icons, and local IBM Plex font
assets. `npm start` runs the Angular development server. Its proxy forwards
`/api` and `/health` to `http://127.0.0.1:8000`, allowing the browser to use
relative API paths without a CORS configuration.

```powershell
cd frontend
npm test -- --watch=false
npm run build
```

The build output is not currently mounted by FastAPI. See
[Configuration and Operations](configuration.md) for the present deployment
boundary.
# Data Health Monitor Documentation

This documentation describes the code that is currently present in this
repository. It is intended to make the system's responsibilities, data flow,
and operational dependencies explicit.

## Reading guide

1. [Architecture](architecture.md) explains the running components, dependency
   direction, persistence, and application lifecycle.
2. [Workflows](workflows.md) follows the main metadata, QA-context, Genie, and
   SQL-execution flows end to end.
3. [API reference](api.md) lists every FastAPI endpoint and its purpose.
4. [Configuration](configuration.md) documents environment settings,
   Databricks prerequisites, local startup, and logging.
5. [Frontend](frontend.md) describes the Angular SPA's implemented routes,
   state, and API use.
6. [Testing](testing.md) maps the test suite and its fixtures.
7. [Legacy Streamlit client](legacy-streamlit.md) records the broader
   proof-of-concept interface that remains in the repository.
8. [Deployment Architecture](../deployment/README.md) records the future Azure
  deployment direction without implementing Azure infrastructure.

## Current implementation boundary

- FastAPI serves the versioned API and `/health`; it does not currently mount
  an Angular build or provide an SPA fallback.
- The Angular application is the current browser frontend, with a dashboard and
  lazy-loaded Unity Catalog browser.
- The legacy Streamlit client implements the fuller test-case-to-SQL workflow
  and talks to FastAPI over HTTP.
- Metadata snapshots persist through SQL Server when the database is configured.
  The JSON repository remains a transitional compatibility implementation for
  direct callers and isolated tests. Test cases, payor configuration, saved
  validation SQL, and execution results remain in configured Databricks SQL tables.

The FastAPI OpenAPI UI is also available at `/docs` whenever the backend is
running.
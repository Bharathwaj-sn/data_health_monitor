# Future Azure Architecture

The intended future runtime flow is:

```text
Angular SPA
  -> FastAPI
  -> SQLAlchemy
  -> pyodbc with Microsoft ODBC Driver 18
  -> Azure SQL Database
```

Azure App Service is a possible FastAPI host. The existing repository guidance
expects FastAPI to serve the compiled Angular static assets in production; Node
is a build-time tool, not a required production server.

Future deployment work may add App Service configuration, Key Vault references,
managed identity, Azure SQL Database, and private networking/VNet integration.
None of those resources or deployment mechanisms are implemented in this
repository at this stage.
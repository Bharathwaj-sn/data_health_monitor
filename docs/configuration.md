# Configuration and Operations

## Configuration source

`backend.config.Settings` reads environment variables and an optional `.env`
file at the repository root. Unknown settings are ignored. Do not commit
Databricks credentials or a populated `.env` file.

## Settings

| Environment variable | Default | Used for |
| --- | --- | --- |
| `APP_DEBUG` | `true` | Parsed into settings. The current FastAPI app explicitly uses `debug=False`, so this setting has no runtime effect today. |
| `APP_LOG_LEVEL` | `INFO` | Overall structured logger threshold. |
| `APP_CONSOLE_LOG_LEVEL` | `ERROR` | Stdout logger threshold. |
| `APP_LOG_FILE` | `logs/data_health_monitor.log` | Rotating JSON log location. Relative paths resolve from the repository root. |
| `APP_LOG_MAX_BYTES` | `10485760` | Maximum size of each log file; must be positive. |
| `APP_LOG_BACKUP_COUNT` | `5` | Number of rotated log archives retained; must be nonnegative. |
| `DATABRICKS_PROFILE` | Unset | Optional named profile passed to `WorkspaceClient`; otherwise the default SDK auth chain is used. |
| `DATABRICKS_CATALOG` | `main` | Default catalog used to execute saved validation SQL. |
| `DATABRICKS_SCHEMA` | `qa` | Default schema used to execute saved validation SQL. |
| `DATABRICKS_WAREHOUSE_ID` | Unset | Required to create a managed Genie space and to run Databricks SQL operations. |
| `TEST_CASE_TABLE_NAME` | `test_cases` | Test-case table name in the default catalog/schema. |
| `PAYOR_CONFIG_CATALOG` | `main` | Payor-configuration catalog. |
| `PAYOR_CONFIG_SCHEMA` | `qa` | Payor-configuration schema. |
| `PAYOR_CONFIG_TABLE_NAME` | `payor_config` | Payor-configuration table name. |
| `VALIDATION_SQL_CATALOG` | `main` | Saved-validation-SQL catalog. |
| `VALIDATION_SQL_SCHEMA` | `qa` | Saved-validation-SQL schema. |
| `VALIDATION_SQL_TABLE_NAME` | `validation_sql` | Saved-validation-SQL table name. The service creates it on save when absent. |
| `TEST_CASE_RESULTS_CATALOG` | `main` | Test-case-results catalog. |
| `TEST_CASE_RESULTS_SCHEMA` | `qa` | Test-case-results schema. |
| `TEST_CASE_RESULTS_TABLE_NAME` | `test_case_results` | Test-case-results table name. The service creates it before first persisted result. |
| `SQL_EXECUTION_TIMEOUT_SECONDS` | `300` | Maximum duration for one saved validation statement. |
| `BATCH_EXECUTION_TIMEOUT_SECONDS` | `1800` | Maximum duration for an ordered batch. |
| `GENIE_SPACE_ID` | Unset | Existing Genie space to manage. The ID is verified during startup. |
| `GENIE_SPACE_TITLE` | Unset | Required at startup. Used to discover an existing space or title a lazily created one. |

Log levels must be one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.

## Local SQL Server

Metadata persistence uses SQLAlchemy 2.x, pyodbc, and Microsoft ODBC Driver 18
for SQL Server. Install the 64-bit ODBC driver on the developer machine, copy
the documented placeholders from `.env.example` into the ignored `.env`, and
set real local database values before calling a metadata endpoint.

| Environment variable | Default | Used for |
| --- | --- | --- |
| `DATABASE_SERVER` | Unset | Local SQL Server host; required when the database is used. |
| `DATABASE_PORT` | `1433` | SQL Server port. |
| `DATABASE_NAME` | Unset | Database name; required when the database is used. |
| `DATABASE_SCHEMA` | `dhm` | Application schema managed by Alembic. |
| `DATABASE_AUTHENTICATION_MODE` | `sql_password` | Current local authentication mode. |
| `DATABASE_USERNAME` | Unset | SQL Server username; required when the database is used. |
| `DATABASE_PASSWORD` | Unset | SQL Server password; required when the database is used. |
| `DATABASE_ODBC_DRIVER` | `ODBC Driver 18 for SQL Server` | pyodbc driver name. |
| `DATABASE_CONNECTION_TIMEOUT_SECONDS` | `30` | ODBC connection timeout. |
| `DATABASE_POOL_SIZE` / `DATABASE_MAX_OVERFLOW` | `5` / `5` | Bounded SQLAlchemy connection pool. |
| `DATABASE_POOL_TIMEOUT_SECONDS` / `DATABASE_POOL_RECYCLE_SECONDS` | `30` / `1800` | Pool wait and recycle limits. |
| `DATABASE_ENCRYPT` | `true` | Enables connection encryption. |
| `DATABASE_TRUST_SERVER_CERTIFICATE` | `false` | Keeps certificate validation enabled by default. |

Run schema changes separately from the application process:

```powershell
.\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
```

Alembic reads the same `Settings` boundary as FastAPI. Do not use
`Base.metadata.create_all()` or run migrations from FastAPI startup.

Before the first migration, verify the configured ODBC connection without
changing the database schema:

```powershell
.\.venv\Scripts\python.exe tests\check_database_connection.py
```

The diagnostic executes only `SELECT 1` and redacts password-like values from
connection failures.

## Databricks prerequisites

The project creates `WorkspaceClient` instances through the Databricks SDK.
Configure authentication on the developer or deployment machine before starting
the app:

```powershell
databricks auth login
databricks auth profiles
databricks current-user me
```

The identity needs access to the Unity Catalog objects it browses or refreshes,
the configured SQL warehouse, the configured operational tables, and the Genie
space APIs. The application does not implement custom authentication and does
not hold secrets in source.

## Local startup

Create an environment and install dependencies from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm ci
cd ..
```

Start FastAPI in one terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Start Angular in another terminal:

```powershell
cd frontend
npm start -- --host 127.0.0.1 --port 4200
```

Use `http://127.0.0.1:4200/dashboard` for Angular,
`http://127.0.0.1:8000/docs` for the generated API documentation, and
`http://127.0.0.1:8000/health` for the liveness response.

## Logging and request tracing

The application logger emits compact JSON. File records include a timestamp,
level, event, safe request fields, and a compact traceback for exceptions.
Request middleware assigns a UUID-like request ID, measures duration, and logs
completion at INFO, WARNING, or ERROR according to status code. Error responses
carry that ID in `X-Request-ID`.

## Deployment boundary

`npm run build` creates Angular static assets, but FastAPI currently does not
serve those assets. A deployed single-process SPA arrangement requires adding a
static-file mount and an SPA fallback to FastAPI, then arranging build artifact
delivery. Until that exists, deploy the API and serve the Angular build through
an appropriate separate static host or web server.
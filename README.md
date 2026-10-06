# Data Health Monitor

FastAPI and Angular application for inspecting Databricks Unity Catalog metadata
and monitoring data-health coverage.

## Architecture

- Angular serves the browser UI during local development
- Angular proxies `/api` and `/health` requests to FastAPI on port 8000
- FastAPI routes delegate to application services
- Databricks services use the Databricks SDK `WorkspaceClient`
- Unity Catalog metadata is read without storing credentials in source control
- Browser state is held in memory and is not persisted locally

## Documentation

The [documentation index](docs/README.md) describes the current architecture,
API surface, operator workflows, configuration, frontend, testing, and the
legacy Streamlit client.

## Local environment setup

### 1. Create a Python virtual environment

From the project root:

```powershell
python -m venv .venv
```

### 2. Install backend dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Install frontend dependencies

```powershell
cd frontend
npm ci
cd ..
```

### 4. Configure Databricks authentication

This project expects the developer machine to already have Databricks OAuth configured through the Databricks CLI or another supported Databricks client auth flow.

```powershell
databricks auth login
```

List the available profiles if needed:

```powershell
databricks auth profiles
```

Then validate the active identity:

```powershell
databricks current-user me
```

### 5. Configure local SQL Server metadata persistence

Install Microsoft ODBC Driver 18 for SQL Server, then copy the database variable
names from `.env.example` to the ignored `.env` file and set the real local SQL
Server values. Do not commit credentials.

Apply the schema after configuring those values:

```powershell
.\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
```

FastAPI does not run migrations automatically. The metadata endpoints use SQL
Server once configured; the former JSON repository remains only for isolated
compatibility tests and direct callers.

The SDK call pattern used in the project follows the working notebook implementation:

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
```

## Run locally

The backend and frontend run in separate terminals.

### Terminal 1: Backend

From the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URLs:

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

### Terminal 2: Frontend

```powershell
cd frontend
npm start -- --host 127.0.0.1 --port 4200
```

Open the Dashboard at http://127.0.0.1:4200/dashboard.

The Angular development server uses `frontend/proxy.conf.json` to forward API
requests to FastAPI. Keep the backend running while using features that load
Databricks or metadata data.

## Application logging

Data Health Monitor writes all configured events to a rotating local file and
only errors to stdout by default. Configure the file and console levels, file
location, rotation size, and retained archives with these environment variables:

```env
APP_LOG_LEVEL=INFO
APP_CONSOLE_LOG_LEVEL=ERROR
APP_LOG_FILE=logs/data_health_monitor.log
APP_LOG_MAX_BYTES=10485760
APP_LOG_BACKUP_COUNT=5
```

The default configuration retains the active log and five archives of up to 10 MiB
each. Local logs are written under `logs/`, which is excluded from source control.

## API endpoints

Data Health Monitor exposes its application API under `/api/v1`.

V1 keeps stable resource IDs in URL paths. Catalog, schema, table, payor, file
type, and search filters are validated JSON request bodies on explicit `POST`
action endpoints. It does not use request bodies with `GET` operations.

- `GET /health`
- `GET /api/v1/databricks/whoami`
- `GET /api/v1/databricks/catalogs`
- `POST /api/v1/databricks/schemas:lookup`
- `POST /api/v1/databricks/schema-objects:lookup`
- `POST /api/v1/databricks/tables:lookup`
- `GET /api/v1/metadata`
- `GET /api/v1/metadata/summary`
- `POST /api/v1/metadata/refresh`
- `GET /api/v1/genie-space/status`

The full contract, including metadata and Genie operations, is available at
http://127.0.0.1:8000/docs.

## Validation

Run backend tests from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Run frontend tests and the production build from `frontend/`:

```powershell
npm test -- --watch=false
npm run build
```

## Notes

- No Databricks secrets are stored in source files.
- No custom authentication logic is implemented.
- `frontend/streamlit_app.py` is retained as the legacy proof-of-concept UI; the
  Angular Dashboard is the current frontend.


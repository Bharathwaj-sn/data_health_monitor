# Database Architecture

Current local persistence uses SQL Server through SQLAlchemy 2.x, pyodbc, and
Microsoft ODBC Driver 18. The metadata repository is injected into FastAPI
services and maps the existing Pydantic metadata contracts to separate
SQLAlchemy ORM entities.

The future target is Azure SQL Database. SQLAlchemy remains the application
database layer, pyodbc remains the SQL Server driver, and Alembic remains the
schema-evolution mechanism. Moving the SQL Server endpoint to Azure SQL should
require configuration and authentication changes, not API, service, or
repository architecture changes.

The current database layer is synchronous. Future high-concurrency or
microservice requirements may justify SQLAlchemy async APIs and an
async-compatible SQL Server driver. That would be an implementation-layer
change; the router, service, and repository boundaries should remain intact.
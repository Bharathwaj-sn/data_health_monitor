# Deployment Architecture

Data Health Monitor is currently in local core development. Azure deployment is
intentionally deferred: this directory captures the future architecture without
creating infrastructure, deployment scripts, or pipelines.

The local SQL Server implementation is the source architecture today. It uses
environment-backed `Settings`, SQLAlchemy, pyodbc, and Alembic so a future host
can supply equivalent configuration without changing application persistence
boundaries.

Read the companion documents before designing Azure resources.
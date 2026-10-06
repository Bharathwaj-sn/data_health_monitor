# Future Migration Process

The intended deployment sequence is:

```text
Build
  -> Test
  -> Run Alembic migrations
  -> Deploy application
  -> Start application
```

FastAPI must never run migrations during application startup. Alembic uses the
same centralized `Settings` configuration as the application, and migrations
should be reviewed before `alembic upgrade head` is run.

A future deployment should use one explicit migration actor, not every App
Service instance. Consider a dedicated migration identity with DDL privileges,
separate from the runtime application identity that requires only data access.
This repository does not implement a CI/CD pipeline or production migration job.
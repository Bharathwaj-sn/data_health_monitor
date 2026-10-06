from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import inspect
from sqlalchemy.engine import Connection
from sqlalchemy.schema import CreateSchema

from backend.config import get_settings
from backend.database.engine import build_database_url, create_database_engine
from backend.database.models import Base


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_schema() -> str:
    return get_settings().database_configuration().schema


def _configure_context(connection: Connection | None = None) -> None:
    database_schema = _database_schema()
    config.attributes["database_schema"] = database_schema
    options = {
        "target_metadata": target_metadata,
        "compare_type": True,
        "version_table_schema": database_schema,
    }
    if connection is None:
        context.configure(
            url=build_database_url(get_settings()),
            literal_binds=True,
            dialect_opts={"paramstyle": "pyformat"},
            **options,
        )
    else:
        context.configure(connection=connection, **options)


def run_migrations_offline() -> None:
    _configure_context()
    with context.begin_transaction():
        context.run_migrations()


def _ensure_schema(connection: Connection, database_schema: str) -> None:
    if not inspect(connection).has_schema(database_schema):
        connection.execute(CreateSchema(database_schema))


def run_migrations_online() -> None:
    engine = create_database_engine(get_settings())
    try:
        with engine.begin() as connection:
            _ensure_schema(connection, _database_schema())
            _configure_context(connection)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
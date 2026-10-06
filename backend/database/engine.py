from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL

from backend.config import Settings, get_settings


_database_engine: Engine | None = None


def build_database_url(settings: Settings) -> URL:
    configuration = settings.database_configuration()
    return URL.create(
        "mssql+pyodbc",
        username=configuration.username,
        password=configuration.password.get_secret_value(),
        host=configuration.server,
        port=configuration.port,
        database=configuration.name,
        query={
            "driver": configuration.odbc_driver,
            "Encrypt": "yes" if configuration.encrypt else "no",
            "TrustServerCertificate": "yes" if configuration.trust_server_certificate else "no",
            "Connection Timeout": str(configuration.connection_timeout_seconds),
            "LongAsMax": "Yes",
        },
    )


def create_database_engine(settings: Settings) -> Engine:
    configuration = settings.database_configuration()
    engine = create_engine(
        build_database_url(settings),
        pool_pre_ping=True,
        pool_size=configuration.pool_size,
        max_overflow=configuration.max_overflow,
        pool_timeout=configuration.pool_timeout_seconds,
        pool_recycle=configuration.pool_recycle_seconds,
        echo=configuration.echo,
    )
    return engine.execution_options(schema_translate_map={None: configuration.schema})


def get_database_engine() -> Engine:
    global _database_engine
    if _database_engine is None:
        _database_engine = create_database_engine(get_settings())
    return _database_engine


def dispose_database_engine() -> None:
    global _database_engine
    if _database_engine is not None:
        _database_engine.dispose()
        _database_engine = None
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL

from backend.config import DatabaseConfiguration, Settings, get_settings


_database_engine: Engine | None = None


def _quote_odbc_value(value: str) -> str:
    return "{" + value.replace("}", "}}") + "}"


def _build_shared_memory_url(configuration: DatabaseConfiguration) -> URL:
    connection_string = ";".join(
        (
            f"DRIVER={_quote_odbc_value(configuration.odbc_driver)}",
            f"SERVER={_quote_odbc_value(f'lpc:{configuration.server}')}",
            f"DATABASE={_quote_odbc_value(configuration.name)}",
            f"UID={_quote_odbc_value(configuration.username)}",
            f"PWD={_quote_odbc_value(configuration.password.get_secret_value())}",
            "Network=DBMSLPCN",
            f"Encrypt={'yes' if configuration.encrypt else 'no'}",
            f"TrustServerCertificate={'yes' if configuration.trust_server_certificate else 'no'}",
            f"Connection Timeout={configuration.connection_timeout_seconds}",
            "LongAsMax=Yes",
        )
    )
    return URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})


def _build_tcp_url(configuration: DatabaseConfiguration) -> URL:
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


def build_database_url(settings: Settings) -> URL:
    configuration = settings.database_configuration()
    if configuration.sql_mode == "SM":
        return _build_shared_memory_url(configuration)
    return _build_tcp_url(configuration)


def create_database_engine(settings: Settings) -> Engine:
    configuration = settings.database_configuration()
    engine = create_engine(
        _build_shared_memory_url(configuration)
        if configuration.sql_mode == "SM"
        else _build_tcp_url(configuration),
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
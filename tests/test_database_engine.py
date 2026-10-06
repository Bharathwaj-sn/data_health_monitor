from backend.config.settings import Settings
from backend.database.engine import create_database_engine


def test_database_engine_uses_configured_pyodbc_connection_options():
    settings = Settings(
        _env_file=None,
        database_server="localhost",
        database_port=1433,
        database_name="data_health_monitor",
        database_schema="dhm",
        database_username="local_user",
        database_password="local_password",
        database_odbc_driver="ODBC Driver 18 for SQL Server",
        database_connection_timeout_seconds=45,
        database_pool_size=3,
        database_max_overflow=2,
    )

    engine = create_database_engine(settings)
    try:
        assert engine.url.get_backend_name() == "mssql"
        assert engine.url.get_driver_name() == "pyodbc"
        assert engine.url.host == "localhost"
        assert engine.url.port == 1433
        assert engine.url.database == "data_health_monitor"
        assert engine.url.query["driver"] == "ODBC Driver 18 for SQL Server"
        assert engine.url.query["Connection Timeout"] == "45"
        assert engine.url.query["Encrypt"] == "yes"
        assert engine.url.query["TrustServerCertificate"] == "no"
        assert engine.pool._pre_ping is True
        assert engine._execution_options["schema_translate_map"][None] == "dhm"
    finally:
        engine.dispose()
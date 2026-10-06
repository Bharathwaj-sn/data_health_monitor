from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.config.settings import Settings


DATABASE_ENVIRONMENT_VARIABLES = (
    "DATABASE_SERVER",
    "DATABASE_PORT",
    "DATABASE_NAME",
    "DATABASE_SCHEMA",
    "DATABASE_AUTHENTICATION_MODE",
    "DATABASE_USERNAME",
    "DATABASE_PASSWORD",
    "DATABASE_ODBC_DRIVER",
    "DATABASE_CONNECTION_TIMEOUT_SECONDS",
    "DATABASE_POOL_SIZE",
    "DATABASE_MAX_OVERFLOW",
    "DATABASE_POOL_TIMEOUT_SECONDS",
    "DATABASE_POOL_RECYCLE_SECONDS",
    "DATABASE_ECHO",
    "DATABASE_ENCRYPT",
    "DATABASE_TRUST_SERVER_CERTIFICATE",
)


def clear_database_environment(monkeypatch) -> None:
    for variable_name in DATABASE_ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(variable_name, raising=False)


def test_database_configuration_loads_from_environment_file(tmp_path: Path, monkeypatch):
    clear_database_environment(monkeypatch)
    environment_file = tmp_path / ".env"
    environment_file.write_text(
        "\n".join(
            [
                "DATABASE_SERVER=localhost",
                "DATABASE_PORT=1433",
                "DATABASE_NAME=data_health_monitor",
                "DATABASE_SCHEMA=dhm",
                "DATABASE_USERNAME=local_user",
                "DATABASE_PASSWORD=local_password",
                "DATABASE_ODBC_DRIVER=ODBC Driver 18 for SQL Server",
            ]
        ),
        encoding="utf-8",
    )

    configuration = Settings(_env_file=environment_file).database_configuration()

    assert configuration.server == "localhost"
    assert configuration.port == 1433
    assert configuration.name == "data_health_monitor"
    assert configuration.schema == "dhm"
    assert configuration.authentication_mode == "sql_password"
    assert configuration.odbc_driver == "ODBC Driver 18 for SQL Server"
    assert configuration.password.get_secret_value() == "local_password"


def test_database_configuration_requires_connection_values(monkeypatch):
    clear_database_environment(monkeypatch)
    settings = Settings(_env_file=None)

    with pytest.raises(ValueError, match="DATABASE_SERVER") as error:
        settings.database_configuration()

    assert "local_password" not in str(error.value)


def test_database_password_is_redacted_from_settings_representation(monkeypatch):
    clear_database_environment(monkeypatch)
    settings = Settings(
        _env_file=None,
        database_server="localhost",
        database_name="data_health_monitor",
        database_username="local_user",
        database_password="local_password",
    )

    assert "local_password" not in repr(settings)
    assert "**********" in repr(settings)


def test_database_pool_settings_are_validated(monkeypatch):
    clear_database_environment(monkeypatch)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_pool_size=0)


@pytest.mark.parametrize("authentication_mode", ["SQL LOGIN", "sql-password", "SQL_AUTHENTICATION"])
def test_database_authentication_mode_normalizes_sql_login_aliases(monkeypatch, authentication_mode: str):
    clear_database_environment(monkeypatch)

    settings = Settings(
        _env_file=None,
        database_server="localhost",
        database_name="data_health_monitor",
        database_username="local_user",
        database_password="local_password",
        database_authentication_mode=authentication_mode,
    )

    assert settings.database_configuration().authentication_mode == "sql_password"
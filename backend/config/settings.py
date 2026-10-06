from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass(frozen=True)
class DatabaseConfiguration:
    server: str
    port: int
    name: str
    schema: str
    authentication_mode: Literal["sql_password"]
    username: str
    password: SecretStr
    odbc_driver: str
    connection_timeout_seconds: int
    pool_size: int
    max_overflow: int
    pool_timeout_seconds: int
    pool_recycle_seconds: int
    echo: bool
    encrypt: bool
    trust_server_certificate: bool


class Settings(BaseSettings):
    app_debug: bool = True
    app_log_level: str = "INFO"
    app_console_log_level: str = "ERROR"
    app_log_file: str = "logs/data_health_monitor.log"
    app_log_max_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    app_log_backup_count: int = Field(default=5, ge=0)
    databricks_profile: str | None = None
    databricks_catalog: str = "main"
    databricks_schema: str = "qa"
    databricks_warehouse_id: str | None = None
    test_case_table_name: str = "test_cases"
    payor_config_catalog: str = "main"
    payor_config_schema: str = "qa"
    payor_config_table_name: str = "payor_config"
    validation_sql_catalog: str = "main"
    validation_sql_schema: str = "qa"
    validation_sql_table_name: str = "validation_sql"
    test_case_results_catalog: str = "main"
    test_case_results_schema: str = "qa"
    test_case_results_table_name: str = "test_case_results"
    sql_execution_timeout_seconds: float = 300
    batch_execution_timeout_seconds: float = 1800
    genie_space_id: str | None = None
    genie_space_title: str | None = None
    database_server: str | None = None
    database_port: int = Field(default=1433, gt=0, le=65535)
    database_name: str | None = None
    database_schema: str = "dhm"
    database_authentication_mode: Literal["sql_password"] = "sql_password"
    database_username: str | None = None
    database_password: SecretStr | None = None
    database_odbc_driver: str = "ODBC Driver 18 for SQL Server"
    database_connection_timeout_seconds: int = Field(default=30, gt=0)
    database_pool_size: int = Field(default=5, gt=0)
    database_max_overflow: int = Field(default=5, ge=0)
    database_pool_timeout_seconds: int = Field(default=30, gt=0)
    database_pool_recycle_seconds: int = Field(default=1800, gt=0)
    database_echo: bool = False
    database_encrypt: bool = True
    database_trust_server_certificate: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("app_log_level", "app_console_log_level")
    @classmethod
    def validate_app_log_level(cls, value: str) -> str:
        normalized_value = value.upper()
        if normalized_value not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("Log levels must be DEBUG, INFO, WARNING, ERROR, or CRITICAL.")
        return normalized_value

    @field_validator(
        "database_server",
        "database_name",
        "database_schema",
        "database_username",
        "database_odbc_driver",
    )
    @classmethod
    def normalize_database_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized_value = value.strip()
        return normalized_value or None

    @field_validator("database_authentication_mode", mode="before")
    @classmethod
    def normalize_database_authentication_mode(cls, value: str) -> str:
        normalized_value = value.strip().lower().replace("_", " ").replace("-", " ")
        if normalized_value in {"sql password", "sql login", "sql authentication"}:
            return "sql_password"
        return normalized_value

    def database_configuration(self) -> DatabaseConfiguration:
        required_values = {
            "DATABASE_SERVER": self.database_server,
            "DATABASE_NAME": self.database_name,
            "DATABASE_USERNAME": self.database_username,
            "DATABASE_PASSWORD": self.database_password,
        }
        missing_values = [name for name, value in required_values.items() if value is None]
        if missing_values:
            raise ValueError(
                "Database configuration is incomplete. Set " + ", ".join(missing_values) + "."
            )

        assert self.database_server is not None
        assert self.database_name is not None
        assert self.database_username is not None
        assert self.database_password is not None

        return DatabaseConfiguration(
            server=self.database_server,
            port=self.database_port,
            name=self.database_name,
            schema=self.database_schema or "dhm",
            authentication_mode=self.database_authentication_mode,
            username=self.database_username,
            password=self.database_password,
            odbc_driver=self.database_odbc_driver or "ODBC Driver 18 for SQL Server",
            connection_timeout_seconds=self.database_connection_timeout_seconds,
            pool_size=self.database_pool_size,
            max_overflow=self.database_max_overflow,
            pool_timeout_seconds=self.database_pool_timeout_seconds,
            pool_recycle_seconds=self.database_pool_recycle_seconds,
            echo=self.database_echo,
            encrypt=self.database_encrypt,
            trust_server_certificate=self.database_trust_server_certificate,
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()

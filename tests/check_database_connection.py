from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import Settings
from backend.database.engine import create_database_engine


def _safe_error_message(error: Exception, password: str) -> str:
    message = str(error)
    for secret in {password, quote_plus(password)}:
        if secret:
            message = message.replace(secret, "********")
    message = re.sub(r"(?i)(pwd|password)=([^;\s]+)", r"\1=********", message)
    return re.sub(r"(//[^:/@]+:)([^@/]+)(@)", r"\1********\3", message)


def check_database_connection() -> int:
    settings: Settings | None = None
    try:
        settings = Settings()
        configuration = settings.database_configuration()
        engine = create_database_engine(settings)
    except Exception as error:
        password = settings.database_password.get_secret_value() if settings and settings.database_password else ""
        print("DATABASE_CONNECTION_FAILED")
        print(f"error_type={type(error).__name__}")
        print(f"error={_safe_error_message(error, password)}")
        return 1

    try:
        with engine.connect() as connection:
            result = connection.scalar(text("SELECT 1"))
        if result != 1:
            raise RuntimeError(f"Unexpected SELECT 1 result: {result!r}")
    except Exception as error:
        print("DATABASE_CONNECTION_FAILED")
        print(f"server={configuration.server}")
        print(f"port={configuration.port}")
        print(f"database={configuration.name}")
        print(f"driver={configuration.odbc_driver}")
        print(f"error_type={type(error).__name__}")
        print(f"error={_safe_error_message(error, configuration.password.get_secret_value())}")
        return 1
    finally:
        engine.dispose()

    print("DATABASE_CONNECTION_OK")
    print(f"server={configuration.server}")
    print(f"port={configuration.port}")
    print(f"database={configuration.name}")
    print(f"schema={configuration.schema}")
    print(f"driver={configuration.odbc_driver}")
    return 0


if __name__ == "__main__":
    raise SystemExit(check_database_connection())
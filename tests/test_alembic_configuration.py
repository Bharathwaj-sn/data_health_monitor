from pathlib import Path

from alembic.config import Config


def test_alembic_configuration_does_not_store_a_database_url():
    configuration = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))

    assert configuration.get_main_option("script_location") == "alembic"
    assert configuration.get_main_option("sqlalchemy.url") == ""
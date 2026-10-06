import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

from backend.config import Settings, get_settings
from backend.database.engine import create_database_engine
from backend.models.metadata import MetadataRefreshInfo, MetadataScope, MetadataTable
from backend.repositories.sql_metadata_repository import SqlMetadataRepository


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_SQLSERVER_INTEGRATION") != "1",
    reason="Set RUN_SQLSERVER_INTEGRATION=1 against an empty dedicated SQL Server test database.",
)


def test_initial_migration_and_sql_metadata_repository():
    get_settings.cache_clear()
    settings = Settings()
    database_configuration = settings.database_configuration()
    alembic_config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))

    command.upgrade(alembic_config, "head")

    engine = create_database_engine(settings)
    try:
        table_names = set(inspect(engine).get_table_names(schema=database_configuration.schema))
        assert {
            "metadata_snapshot",
            "metadata_catalog",
            "metadata_schema",
            "metadata_table",
            "metadata_column",
            "metadata_volume",
        } <= table_names

        session = sessionmaker(bind=engine, expire_on_commit=False)()
        try:
            repository = SqlMetadataRepository(session)
            refreshed_at = datetime.now(timezone.utc)
            refresh = MetadataRefreshInfo(
                refreshed_at=refreshed_at,
                scope=MetadataScope(
                    type="table",
                    catalog_name="main",
                    schema_name="qa",
                    table_name="claims",
                ),
            )
            snapshot = repository.save_scope_metadata(
                refresh.scope,
                MetadataTable(
                    catalog_name="main",
                    schema_name="qa",
                    name="claims",
                    metadata={"refreshed_at": refreshed_at},
                    columns=[{"name": "claim_id", "type_name": "BIGINT", "nullable": False}],
                ),
                refresh,
            )

            table = repository.get_table_metadata("main", "qa", "CLAIMS")

            assert snapshot.refresh.scope == refresh.scope
            assert table.name == "claims"
            assert table.columns[0].name == "claim_id"
        finally:
            session.close()
    finally:
        engine.dispose()
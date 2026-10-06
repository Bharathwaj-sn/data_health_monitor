from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.database.engine import get_database_engine
from backend.database.models import (
    MetadataCatalogRecord,
    MetadataColumnRecord,
    MetadataSchemaRecord,
    MetadataSnapshotRecord,
    MetadataTableRecord,
    MetadataVolumeRecord,
)
from backend.models.metadata import (
    MetadataCatalog,
    MetadataColumn,
    MetadataNode,
    MetadataRefreshInfo,
    MetadataSchema,
    MetadataScope,
    MetadataSnapshot,
    MetadataTable,
    MetadataVolume,
)
from backend.repositories.metadata_repository import MetadataSnapshotNotFoundError, MetadataTableNotFoundError


class SqlMetadataRepository:
    def __init__(self, session: Session):
        self._session = session

    @property
    def session(self) -> Session:
        if self._session.bind is None:
            self._session.bind = get_database_engine()
        return self._session

    @staticmethod
    def _snapshot_options():
        return (
            selectinload(MetadataSnapshotRecord.catalogs)
            .selectinload(MetadataCatalogRecord.schemas)
            .selectinload(MetadataSchemaRecord.tables)
            .selectinload(MetadataTableRecord.columns),
            selectinload(MetadataSnapshotRecord.catalogs)
            .selectinload(MetadataCatalogRecord.schemas)
            .selectinload(MetadataSchemaRecord.volumes),
        )

    def _load_snapshot_record(self) -> MetadataSnapshotRecord | None:
        return self.session.scalar(
            select(MetadataSnapshotRecord).options(*self._snapshot_options()).order_by(MetadataSnapshotRecord.id)
        )

    @staticmethod
    def _catalog_model(record: MetadataCatalogRecord) -> MetadataCatalog:
        return MetadataCatalog(
            name=record.name,
            metadata=MetadataNode(refreshed_at=record.refreshed_at),
            schemas=[SqlMetadataRepository._schema_model(schema) for schema in record.schemas],
        )

    @staticmethod
    def _schema_model(record: MetadataSchemaRecord) -> MetadataSchema:
        return MetadataSchema(
            name=record.name,
            metadata=MetadataNode(refreshed_at=record.refreshed_at),
            tables=[SqlMetadataRepository._table_model(record.catalog.name, record.name, table) for table in record.tables],
            volumes=[MetadataVolume(name=volume.name) for volume in record.volumes],
        )

    @staticmethod
    def _table_model(catalog_name: str, schema_name: str, record: MetadataTableRecord) -> MetadataTable:
        return MetadataTable(
            catalog_name=catalog_name,
            schema_name=schema_name,
            name=record.name,
            metadata=MetadataNode(refreshed_at=record.refreshed_at),
            table_type=record.table_type,
            data_source_format=record.data_source_format,
            comment=record.comment,
            storage_location=record.storage_location,
            columns=[
                MetadataColumn(
                    name=column.name,
                    type_name=column.type_name,
                    type_text=column.type_text,
                    nullable=column.nullable,
                    position=column.position,
                    comment=column.comment,
                )
                for column in record.columns
            ],
        )

    @classmethod
    def _snapshot_model(cls, record: MetadataSnapshotRecord) -> MetadataSnapshot:
        scope = None
        if record.refresh_scope_type is not None and record.refresh_catalog_name is not None:
            scope = MetadataScope.model_validate(
                {
                    "type": record.refresh_scope_type,
                    "catalog_name": record.refresh_catalog_name,
                    "schema_name": record.refresh_schema_name,
                    "table_name": record.refresh_table_name,
                }
            )
        return MetadataSnapshot(
            metadata_version=record.metadata_version,
            refresh=MetadataRefreshInfo.model_validate(
                {
                    "status": record.refresh_status,
                    "refreshed_at": record.refresh_refreshed_at or datetime.now().astimezone(),
                    "duration_ms": record.refresh_duration_ms,
                    "scope": scope,
                }
            ),
            catalogs=[cls._catalog_model(catalog) for catalog in record.catalogs],
        )

    @staticmethod
    def _column_record(model: MetadataColumn) -> MetadataColumnRecord:
        return MetadataColumnRecord(
            name=model.name,
            type_name=model.type_name,
            type_text=model.type_text,
            nullable=model.nullable,
            position=model.position,
            comment=model.comment,
        )

    @classmethod
    def _table_record(cls, model: MetadataTable) -> MetadataTableRecord:
        return MetadataTableRecord(
            name=model.name,
            refreshed_at=model.metadata.refreshed_at,
            table_type=model.table_type,
            data_source_format=model.data_source_format,
            comment=model.comment,
            storage_location=model.storage_location,
            columns=[cls._column_record(column) for column in model.columns],
        )

    @classmethod
    def _schema_record(cls, model: MetadataSchema) -> MetadataSchemaRecord:
        return MetadataSchemaRecord(
            name=model.name,
            refreshed_at=model.metadata.refreshed_at,
            tables=[cls._table_record(table) for table in model.tables],
            volumes=[MetadataVolumeRecord(name=volume.name) for volume in model.volumes],
        )

    @classmethod
    def _catalog_record(cls, model: MetadataCatalog) -> MetadataCatalogRecord:
        return MetadataCatalogRecord(
            name=model.name,
            refreshed_at=model.metadata.refreshed_at,
            schemas=[cls._schema_record(schema) for schema in model.schemas],
        )

    @staticmethod
    def _find_catalog(snapshot: MetadataSnapshotRecord, catalog_name: str) -> MetadataCatalogRecord | None:
        return next((catalog for catalog in snapshot.catalogs if catalog.name == catalog_name), None)

    @staticmethod
    def _find_schema(catalog: MetadataCatalogRecord, schema_name: str) -> MetadataSchemaRecord | None:
        return next((schema for schema in catalog.schemas if schema.name == schema_name), None)

    @staticmethod
    def _find_table(schema: MetadataSchemaRecord, table_name: str) -> MetadataTableRecord | None:
        return next((table for table in schema.tables if table.name.casefold() == table_name.casefold()), None)

    def _replace_table(self, schema: MetadataSchemaRecord, model: MetadataTable) -> None:
        record = self._find_table(schema, model.name)
        if record is None:
            schema.tables.append(self._table_record(model))
            return

        record.name = model.name
        record.refreshed_at = model.metadata.refreshed_at
        record.table_type = model.table_type
        record.data_source_format = model.data_source_format
        record.comment = model.comment
        record.storage_location = model.storage_location
        record.columns.clear()
        self.session.flush()
        record.columns.extend(self._column_record(column) for column in model.columns)

    def _replace_schema(self, catalog: MetadataCatalogRecord, model: MetadataSchema) -> None:
        record = self._find_schema(catalog, model.name)
        if record is None:
            catalog.schemas.append(self._schema_record(model))
            return

        record.refreshed_at = model.metadata.refreshed_at
        record.tables.clear()
        record.volumes.clear()
        self.session.flush()
        record.tables.extend(self._table_record(table) for table in model.tables)
        record.volumes.extend(MetadataVolumeRecord(name=volume.name) for volume in model.volumes)

    def _replace_catalog(self, snapshot: MetadataSnapshotRecord, model: MetadataCatalog) -> None:
        record = self._find_catalog(snapshot, model.name)
        if record is None:
            snapshot.catalogs.append(self._catalog_record(model))
            return

        record.refreshed_at = model.metadata.refreshed_at
        record.schemas.clear()
        self.session.flush()
        record.schemas.extend(self._schema_record(schema) for schema in model.schemas)

    @staticmethod
    def _set_refresh(record: MetadataSnapshotRecord, refresh: MetadataRefreshInfo) -> None:
        record.refresh_status = refresh.status
        record.refresh_refreshed_at = refresh.refreshed_at
        record.refresh_duration_ms = refresh.duration_ms
        record.refresh_scope_type = refresh.scope.type if refresh.scope else None
        record.refresh_catalog_name = refresh.scope.catalog_name if refresh.scope else None
        record.refresh_schema_name = refresh.scope.schema_name if refresh.scope else None
        record.refresh_table_name = refresh.scope.table_name if refresh.scope else None

    def save_scope_metadata(
        self,
        scope: MetadataScope,
        metadata: MetadataCatalog | MetadataSchema | MetadataTable,
        refresh: MetadataRefreshInfo,
    ) -> MetadataSnapshot:
        with self.session.begin():
            snapshot = self._load_snapshot_record()
            if snapshot is None:
                snapshot = MetadataSnapshotRecord(
                    id=1,
                    metadata_version="1.0",
                    refresh_status="SUCCESS",
                )
                self.session.add(snapshot)
                self.session.flush()

            if scope.type == "catalog":
                if not isinstance(metadata, MetadataCatalog):
                    raise TypeError("Catalog refreshes require MetadataCatalog persistence data.")
                self._replace_catalog(snapshot, metadata)
            elif scope.type == "schema":
                if not isinstance(metadata, MetadataSchema):
                    raise TypeError("Schema refreshes require MetadataSchema persistence data.")
                assert scope.schema_name is not None
                catalog = self._find_catalog(snapshot, scope.catalog_name)
                if catalog is None:
                    catalog = MetadataCatalogRecord(name=scope.catalog_name)
                    snapshot.catalogs.append(catalog)
                self._replace_schema(catalog, metadata)
            else:
                if not isinstance(metadata, MetadataTable):
                    raise TypeError("Table refreshes require MetadataTable persistence data.")
                assert scope.schema_name is not None
                catalog = self._find_catalog(snapshot, scope.catalog_name)
                if catalog is None:
                    catalog = MetadataCatalogRecord(name=scope.catalog_name)
                    snapshot.catalogs.append(catalog)
                schema = self._find_schema(catalog, scope.schema_name)
                if schema is None:
                    schema = MetadataSchemaRecord(name=scope.schema_name)
                    catalog.schemas.append(schema)
                self._replace_table(schema, metadata)

            self._set_refresh(snapshot, refresh)
            self.session.flush()
            return self._snapshot_model(snapshot)

    def load_snapshot(self) -> MetadataSnapshot | None:
        snapshot = self._load_snapshot_record()
        return self._snapshot_model(snapshot) if snapshot else None

    def get_table_metadata(self, catalog_name: str, schema_name: str, table_name: str) -> MetadataTable:
        snapshot = self.load_snapshot()
        if snapshot is None:
            raise MetadataSnapshotNotFoundError("No metadata snapshot has been generated yet.")

        for catalog in snapshot.catalogs:
            if catalog.name != catalog_name:
                continue
            for schema in catalog.schemas:
                if schema.name != schema_name:
                    continue
                for table in schema.tables:
                    if table.name.casefold() == table_name.casefold():
                        return table
        raise MetadataTableNotFoundError(catalog_name, schema_name, table_name)

    def get_summary(self) -> dict:
        snapshot = self.load_snapshot()
        if snapshot is None:
            return {
                "catalog_count": 0,
                "schema_count": 0,
                "table_count": 0,
                "volume_count": 0,
                "last_refreshed_at": None,
                "status": "SUCCESS",
            }

        catalogs = snapshot.catalogs
        schemas = [schema for catalog in catalogs for schema in catalog.schemas]
        tables = [table for schema in schemas for table in schema.tables]
        last_refreshed_at = next(
            (
                table.metadata.refreshed_at.isoformat()
                for table in tables
                if table.metadata.refreshed_at is not None
            ),
            None,
        )
        if last_refreshed_at is None:
            last_refreshed_at = next(
                (
                    catalog.metadata.refreshed_at.isoformat()
                    for catalog in catalogs
                    if catalog.metadata.refreshed_at is not None
                ),
                None,
            )
        return {
            "catalog_count": len(catalogs),
            "schema_count": len(schemas),
            "table_count": len(tables),
            "volume_count": sum(len(schema.volumes) for schema in schemas),
            "last_refreshed_at": last_refreshed_at,
            "status": snapshot.refresh.status,
        }
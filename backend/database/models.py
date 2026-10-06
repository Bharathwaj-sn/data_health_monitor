from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, MetaData, Unicode, UnicodeText, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class MetadataSnapshotRecord(Base):
    __tablename__ = "metadata_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metadata_version: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    refresh_status: Mapped[str] = mapped_column(Unicode(16), nullable=False)
    refresh_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refresh_duration_ms: Mapped[int | None] = mapped_column(Integer)
    refresh_scope_type: Mapped[str | None] = mapped_column(Unicode(16))
    refresh_catalog_name: Mapped[str | None] = mapped_column(Unicode(255))
    refresh_schema_name: Mapped[str | None] = mapped_column(Unicode(255))
    refresh_table_name: Mapped[str | None] = mapped_column(Unicode(255))

    catalogs: Mapped[list[MetadataCatalogRecord]] = relationship(
        back_populates="snapshot",
        cascade="all, delete-orphan",
        order_by="MetadataCatalogRecord.id",
    )


class MetadataCatalogRecord(Base):
    __tablename__ = "metadata_catalog"
    __table_args__ = (UniqueConstraint("snapshot_id", "name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("metadata_snapshot.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    snapshot: Mapped[MetadataSnapshotRecord] = relationship(back_populates="catalogs")
    schemas: Mapped[list[MetadataSchemaRecord]] = relationship(
        back_populates="catalog",
        cascade="all, delete-orphan",
        order_by="MetadataSchemaRecord.id",
    )


class MetadataSchemaRecord(Base):
    __tablename__ = "metadata_schema"
    __table_args__ = (UniqueConstraint("catalog_id", "name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    catalog_id: Mapped[int] = mapped_column(
        ForeignKey("metadata_catalog.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    catalog: Mapped[MetadataCatalogRecord] = relationship(back_populates="schemas")
    tables: Mapped[list[MetadataTableRecord]] = relationship(
        back_populates="schema",
        cascade="all, delete-orphan",
        order_by="MetadataTableRecord.id",
    )
    volumes: Mapped[list[MetadataVolumeRecord]] = relationship(
        back_populates="schema",
        cascade="all, delete-orphan",
        order_by="MetadataVolumeRecord.id",
    )


class MetadataTableRecord(Base):
    __tablename__ = "metadata_table"
    __table_args__ = (
        UniqueConstraint("schema_id", "name"),
        Index("ix_metadata_table_schema_name", "schema_id", "name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schema_id: Mapped[int] = mapped_column(
        ForeignKey("metadata_schema.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    table_type: Mapped[str | None] = mapped_column(Unicode(128))
    data_source_format: Mapped[str | None] = mapped_column(Unicode(128))
    comment: Mapped[str | None] = mapped_column(UnicodeText)
    storage_location: Mapped[str | None] = mapped_column(UnicodeText)

    schema: Mapped[MetadataSchemaRecord] = relationship(back_populates="tables")
    columns: Mapped[list[MetadataColumnRecord]] = relationship(
        back_populates="table",
        cascade="all, delete-orphan",
        order_by="MetadataColumnRecord.id",
    )


class MetadataColumnRecord(Base):
    __tablename__ = "metadata_column"
    __table_args__ = (
        UniqueConstraint("table_id", "name"),
        Index("ix_metadata_column_table_position", "table_id", "position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_id: Mapped[int] = mapped_column(
        ForeignKey("metadata_table.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    type_name: Mapped[str | None] = mapped_column(Unicode(255))
    type_text: Mapped[str | None] = mapped_column(UnicodeText)
    nullable: Mapped[bool | None] = mapped_column()
    position: Mapped[int | None] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(UnicodeText)

    table: Mapped[MetadataTableRecord] = relationship(back_populates="columns")


class MetadataVolumeRecord(Base):
    __tablename__ = "metadata_volume"
    __table_args__ = (UniqueConstraint("schema_id", "name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schema_id: Mapped[int] = mapped_column(
        ForeignKey("metadata_schema.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Unicode(255), nullable=False)

    schema: Mapped[MetadataSchemaRecord] = relationship(back_populates="volumes")
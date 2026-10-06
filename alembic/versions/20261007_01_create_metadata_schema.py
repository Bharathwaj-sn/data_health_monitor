"""Create metadata persistence schema.

Revision ID: 20261007_01
Revises:
Create Date: 2026-10-07 00:00:00.000000
"""

from alembic import context, op
import sqlalchemy as sa


revision = "20261007_01"
down_revision = None
branch_labels = None
depends_on = None


def _database_schema() -> str:
    return str(context.get_context().config.attributes["database_schema"])


def upgrade() -> None:
    schema = _database_schema()
    op.create_table(
        "metadata_snapshot",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("metadata_version", sa.Unicode(length=32), nullable=False),
        sa.Column("refresh_status", sa.Unicode(length=16), nullable=False),
        sa.Column("refresh_refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refresh_duration_ms", sa.Integer(), nullable=True),
        sa.Column("refresh_scope_type", sa.Unicode(length=16), nullable=True),
        sa.Column("refresh_catalog_name", sa.Unicode(length=255), nullable=True),
        sa.Column("refresh_schema_name", sa.Unicode(length=255), nullable=True),
        sa.Column("refresh_table_name", sa.Unicode(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_metadata_snapshot"),
        schema=schema,
    )
    op.create_table(
        "metadata_catalog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Unicode(length=255), nullable=False),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            [f"{schema}.metadata_snapshot.id"],
            name="fk_metadata_catalog_snapshot_id_metadata_snapshot",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_metadata_catalog"),
        sa.UniqueConstraint("snapshot_id", "name", name="uq_metadata_catalog_snapshot_id"),
        schema=schema,
    )
    op.create_table(
        "metadata_schema",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("catalog_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Unicode(length=255), nullable=False),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["catalog_id"],
            [f"{schema}.metadata_catalog.id"],
            name="fk_metadata_schema_catalog_id_metadata_catalog",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_metadata_schema"),
        sa.UniqueConstraint("catalog_id", "name", name="uq_metadata_schema_catalog_id"),
        schema=schema,
    )
    op.create_table(
        "metadata_table",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("schema_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Unicode(length=255), nullable=False),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("table_type", sa.Unicode(length=128), nullable=True),
        sa.Column("data_source_format", sa.Unicode(length=128), nullable=True),
        sa.Column("comment", sa.UnicodeText(), nullable=True),
        sa.Column("storage_location", sa.UnicodeText(), nullable=True),
        sa.ForeignKeyConstraint(
            ["schema_id"],
            [f"{schema}.metadata_schema.id"],
            name="fk_metadata_table_schema_id_metadata_schema",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_metadata_table"),
        sa.UniqueConstraint("schema_id", "name", name="uq_metadata_table_schema_id"),
        schema=schema,
    )
    op.create_index("ix_metadata_table_schema_name", "metadata_table", ["schema_id", "name"], schema=schema)
    op.create_table(
        "metadata_column",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Unicode(length=255), nullable=False),
        sa.Column("type_name", sa.Unicode(length=255), nullable=True),
        sa.Column("type_text", sa.UnicodeText(), nullable=True),
        sa.Column("nullable", sa.Boolean(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("comment", sa.UnicodeText(), nullable=True),
        sa.ForeignKeyConstraint(
            ["table_id"],
            [f"{schema}.metadata_table.id"],
            name="fk_metadata_column_table_id_metadata_table",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_metadata_column"),
        sa.UniqueConstraint("table_id", "name", name="uq_metadata_column_table_id"),
        schema=schema,
    )
    op.create_index(
        "ix_metadata_column_table_position",
        "metadata_column",
        ["table_id", "position"],
        schema=schema,
    )
    op.create_table(
        "metadata_volume",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("schema_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Unicode(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["schema_id"],
            [f"{schema}.metadata_schema.id"],
            name="fk_metadata_volume_schema_id_metadata_schema",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_metadata_volume"),
        sa.UniqueConstraint("schema_id", "name", name="uq_metadata_volume_schema_id"),
        schema=schema,
    )


def downgrade() -> None:
    schema = _database_schema()
    op.drop_table("metadata_volume", schema=schema)
    op.drop_index("ix_metadata_column_table_position", table_name="metadata_column", schema=schema)
    op.drop_table("metadata_column", schema=schema)
    op.drop_index("ix_metadata_table_schema_name", table_name="metadata_table", schema=schema)
    op.drop_table("metadata_table", schema=schema)
    op.drop_table("metadata_schema", schema=schema)
    op.drop_table("metadata_catalog", schema=schema)
    op.drop_table("metadata_snapshot", schema=schema)
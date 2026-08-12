"""postgresql baseline

Revision ID: 20260812_0001
Revises: None
Create Date: 2026-08-12 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260812_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "datatypes",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("namespace", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("namespace", "name", name="uq_datatypes_name"),
    )
    op.create_table(
        "object_templates",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("namespace", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("abstract", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("namespace", "name", name="uq_object_templates_name"),
    )
    op.create_table(
        "datatype_versions",
        sa.Column("datatype_id", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("base_type", sa.Text(), nullable=False),
        sa.Column("constraints_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["datatype_id"],
            ["datatypes.id"],
            name=op.f("fk_datatype_versions_datatype_id_datatypes"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("datatype_id", "version", name="pk_datatype_versions"),
    )
    op.create_table(
        "object_template_versions",
        sa.Column("template_id", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("parent_template_id", sa.Text(), nullable=True),
        sa.Column("parent_version", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "("
            "(parent_template_id IS NULL AND parent_version IS NULL) "
            "OR "
            "(parent_template_id IS NOT NULL AND parent_version IS NOT NULL)"
            ")",
            name="ck_object_template_versions_parent_pair",
        ),
        sa.ForeignKeyConstraint(
            ["parent_template_id", "parent_version"],
            ["object_template_versions.template_id", "object_template_versions.version"],
            name="fk_object_template_versions_parent",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["object_templates.id"],
            name=op.f("fk_object_template_versions_template_id_object_templates"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("template_id", "version", name="pk_object_template_versions"),
    )
    op.create_index(
        "ix_object_template_versions_parent",
        "object_template_versions",
        ["parent_template_id", "parent_version"],
        unique=False,
    )
    op.create_table(
        "relationship_definitions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("source_template_id", sa.Text(), nullable=False),
        sa.Column("target_template_id", sa.Text(), nullable=False),
        sa.Column("forward_name", sa.Text(), nullable=False),
        sa.Column("reverse_name", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_template_id"],
            ["object_templates.id"],
            name=op.f("fk_relationship_definitions_source_template_id_object_templates"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_template_id"],
            ["object_templates.id"],
            name=op.f("fk_relationship_definitions_target_template_id_object_templates"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "object_template_components",
        sa.Column("template_id", sa.Text(), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("target_template_id", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["target_template_id"],
            ["object_templates.id"],
            name="fk_object_template_components_target_template",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["template_id", "template_version"],
            ["object_template_versions.template_id", "object_template_versions.version"],
            name="fk_object_template_components_owner",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "template_id",
            "template_version",
            "name",
            name="pk_object_template_components",
        ),
        sa.UniqueConstraint(
            "template_id",
            "template_version",
            "position",
            name="uq_object_template_components_owner_position",
        ),
    )
    op.create_index(
        "ix_object_template_components_target_template",
        "object_template_components",
        ["target_template_id"],
        unique=False,
    )
    op.create_table(
        "object_template_properties",
        sa.Column("template_id", sa.Text(), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("datatype_id", sa.Text(), nullable=False),
        sa.Column("datatype_version", sa.Integer(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["datatype_id", "datatype_version"],
            ["datatype_versions.datatype_id", "datatype_versions.version"],
            name="fk_object_template_properties_datatype_version",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["template_id", "template_version"],
            ["object_template_versions.template_id", "object_template_versions.version"],
            name="fk_object_template_properties_owner",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "template_id",
            "template_version",
            "name",
            name="pk_object_template_properties",
        ),
        sa.UniqueConstraint(
            "template_id",
            "template_version",
            "position",
            name="uq_object_template_properties_owner_position",
        ),
    )
    op.create_index(
        "ix_object_template_properties_datatype_version",
        "object_template_properties",
        ["datatype_id", "datatype_version"],
        unique=False,
    )
    op.create_table(
        "objects",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("template_id", sa.Text(), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False),
        sa.Column("properties_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["template_id", "template_version"],
            ["object_template_versions.template_id", "object_template_versions.version"],
            name="fk_objects_template_version",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_objects_template_version",
        "objects",
        ["template_id", "template_version"],
        unique=False,
    )
    op.create_table(
        "object_changes",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("object_id", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("before_json", sa.Text(), nullable=True),
        sa.Column("after_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_object_changes_object_id_occurred_at",
        "object_changes",
        ["object_id", "occurred_at"],
        unique=False,
    )
    op.create_table(
        "object_components",
        sa.Column("parent_object_id", sa.Text(), nullable=False),
        sa.Column("slot_name", sa.Text(), nullable=False),
        sa.Column("child_object_id", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "parent_object_id <> child_object_id",
            name="ck_object_components_distinct_objects",
        ),
        sa.CheckConstraint(
            "slot_name <> ''",
            name="ck_object_components_slot_name_not_empty",
        ),
        sa.ForeignKeyConstraint(
            ["child_object_id"],
            ["objects.id"],
            name="fk_object_components_child_object_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_object_id"],
            ["objects.id"],
            name="fk_object_components_parent_object_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("child_object_id"),
    )
    op.create_index(
        "ix_object_components_parent_slot_child",
        "object_components",
        ["parent_object_id", "slot_name", "child_object_id"],
        unique=False,
    )
    op.create_table(
        "relationships",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("relationship_definition_id", sa.Text(), nullable=False),
        sa.Column("source_object_id", sa.Text(), nullable=False),
        sa.Column("target_object_id", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["relationship_definition_id"],
            ["relationship_definitions.id"],
            name=op.f("fk_relationships_relationship_definition_id_relationship_definitions"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_object_id"],
            ["objects.id"],
            name=op.f("fk_relationships_source_object_id_objects"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_object_id"],
            ["objects.id"],
            name=op.f("fk_relationships_target_object_id_objects"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "relationship_definition_id",
            "source_object_id",
            "target_object_id",
            name="uq_relationships_definition_source_target",
        ),
    )


def downgrade() -> None:
    op.drop_table("relationships")
    op.drop_index("ix_object_components_parent_slot_child", table_name="object_components")
    op.drop_table("object_components")
    op.drop_index("ix_object_changes_object_id_occurred_at", table_name="object_changes")
    op.drop_table("object_changes")
    op.drop_index("ix_objects_template_version", table_name="objects")
    op.drop_table("objects")
    op.drop_index(
        "ix_object_template_properties_datatype_version",
        table_name="object_template_properties",
    )
    op.drop_table("object_template_properties")
    op.drop_index(
        "ix_object_template_components_target_template",
        table_name="object_template_components",
    )
    op.drop_table("object_template_components")
    op.drop_table("relationship_definitions")
    op.drop_index("ix_object_template_versions_parent", table_name="object_template_versions")
    op.drop_table("object_template_versions")
    op.drop_table("datatype_versions")
    op.drop_table("object_templates")
    op.drop_table("datatypes")

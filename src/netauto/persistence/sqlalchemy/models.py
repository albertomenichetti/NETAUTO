"""SQLAlchemy row models for datatype, object template, relationship, and object persistence."""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from netauto.persistence.sqlalchemy.base import Base


class DataTypeRow(Base):
    """Persisted datatype identity row."""

    __tablename__ = "datatypes"
    __table_args__ = (UniqueConstraint("namespace", "name", name="uq_datatypes_name"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    namespace: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class DataTypeVersionRow(Base):
    """Persisted datatype version row."""

    __tablename__ = "datatype_versions"
    __table_args__ = (
        PrimaryKeyConstraint("datatype_id", "version", name="pk_datatype_versions"),
    )

    datatype_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("datatypes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    base_type: Mapped[str] = mapped_column(Text, nullable=False)
    constraints_json: Mapped[str] = mapped_column(Text, nullable=False)


class ObjectTemplateRow(Base):
    """Persisted object template identity row."""

    __tablename__ = "object_templates"
    __table_args__ = (
        UniqueConstraint("namespace", "name", name="uq_object_templates_name"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    namespace: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    abstract: Mapped[bool] = mapped_column(Boolean, nullable=False)


class ObjectTemplateVersionRow(Base):
    """Persisted object template version row."""

    __tablename__ = "object_template_versions"
    __table_args__ = (
        PrimaryKeyConstraint("template_id", "version", name="pk_object_template_versions"),
        ForeignKeyConstraint(
            ["parent_template_id", "parent_version"],
            ["object_template_versions.template_id", "object_template_versions.version"],
            ondelete="RESTRICT",
            name="fk_object_template_versions_parent",
        ),
        CheckConstraint(
            "("
            "(parent_template_id IS NULL AND parent_version IS NULL) "
            "OR "
            "(parent_template_id IS NOT NULL AND parent_version IS NOT NULL)"
            ")",
            name="ck_object_template_versions_parent_pair",
        ),
        Index(
            "ix_object_template_versions_parent",
            "parent_template_id",
            "parent_version",
        ),
    )

    template_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("object_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    parent_template_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_version: Mapped[int | None] = mapped_column(nullable=True)


class ObjectTemplatePropertyRow(Base):
    """Persisted exact object template property declaration row."""

    __tablename__ = "object_template_properties"
    __table_args__ = (
        PrimaryKeyConstraint(
            "template_id",
            "template_version",
            "name",
            name="pk_object_template_properties",
        ),
        UniqueConstraint(
            "template_id",
            "template_version",
            "position",
            name="uq_object_template_properties_owner_position",
        ),
        ForeignKeyConstraint(
            ["template_id", "template_version"],
            ["object_template_versions.template_id", "object_template_versions.version"],
            ondelete="CASCADE",
            name="fk_object_template_properties_owner",
        ),
        ForeignKeyConstraint(
            ["datatype_id", "datatype_version"],
            ["datatype_versions.datatype_id", "datatype_versions.version"],
            ondelete="RESTRICT",
            name="fk_object_template_properties_datatype_version",
        ),
        Index(
            "ix_object_template_properties_datatype_version",
            "datatype_id",
            "datatype_version",
        ),
    )

    template_id: Mapped[str] = mapped_column(Text, nullable=False)
    template_version: Mapped[int] = mapped_column(nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    datatype_id: Mapped[str] = mapped_column(Text, nullable=False)
    datatype_version: Mapped[int] = mapped_column(nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False)


class ObjectTemplateComponentRow(Base):
    """Persisted stable-identity object template component declaration row."""

    __tablename__ = "object_template_components"
    __table_args__ = (
        PrimaryKeyConstraint(
            "template_id",
            "template_version",
            "name",
            name="pk_object_template_components",
        ),
        UniqueConstraint(
            "template_id",
            "template_version",
            "position",
            name="uq_object_template_components_owner_position",
        ),
        ForeignKeyConstraint(
            ["template_id", "template_version"],
            ["object_template_versions.template_id", "object_template_versions.version"],
            ondelete="CASCADE",
            name="fk_object_template_components_owner",
        ),
        ForeignKeyConstraint(
            ["target_template_id"],
            ["object_templates.id"],
            ondelete="RESTRICT",
            name="fk_object_template_components_target_template",
        ),
        Index(
            "ix_object_template_components_target_template",
            "target_template_id",
        ),
    )

    template_id: Mapped[str] = mapped_column(Text, nullable=False)
    template_version: Mapped[int] = mapped_column(nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    target_template_id: Mapped[str] = mapped_column(Text, nullable=False)


class RelationshipDefinitionRow(Base):
    """Persisted relationship definition row."""

    __tablename__ = "relationship_definitions"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    source_template_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("object_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    target_template_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("object_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    forward_name: Mapped[str] = mapped_column(Text, nullable=False)
    reverse_name: Mapped[str] = mapped_column(Text, nullable=False)


class RelationshipRow(Base):
    """Persisted runtime relationship row."""

    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint(
            "relationship_definition_id",
            "source_object_id",
            "target_object_id",
            name="uq_relationships_definition_source_target",
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    relationship_definition_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("relationship_definitions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_object_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("objects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    target_object_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("objects.id", ondelete="RESTRICT"),
        nullable=False,
    )


class ObjectRow(Base):
    """Persisted object snapshot row."""

    __tablename__ = "objects"
    __table_args__ = (
        ForeignKeyConstraint(
            ["template_id", "template_version"],
            ["object_template_versions.template_id", "object_template_versions.version"],
            ondelete="RESTRICT",
            name="fk_objects_template_version",
        ),
        Index("ix_objects_template_version", "template_id", "template_version"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    template_id: Mapped[str] = mapped_column(Text, nullable=False)
    template_version: Mapped[int] = mapped_column(nullable=False)
    properties_json: Mapped[str] = mapped_column(Text, nullable=False)


class ObjectChangeRow(Base):
    """Persisted append-only object history row."""

    __tablename__ = "object_changes"
    __table_args__ = (
        Index("ix_object_changes_object_id_occurred_at", "object_id", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    object_id: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    before_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class ObjectComponentRow(Base):
    """Persisted direct structural ownership edge row."""

    __tablename__ = "object_components"
    __table_args__ = (
        ForeignKeyConstraint(
            ["parent_object_id"],
            ["objects.id"],
            ondelete="CASCADE",
            name="fk_object_components_parent_object_id",
        ),
        ForeignKeyConstraint(
            ["child_object_id"],
            ["objects.id"],
            ondelete="CASCADE",
            name="fk_object_components_child_object_id",
        ),
        CheckConstraint(
            "parent_object_id <> child_object_id",
            name="ck_object_components_distinct_objects",
        ),
        CheckConstraint(
            "slot_name <> ''",
            name="ck_object_components_slot_name_not_empty",
        ),
        Index(
            "ix_object_components_parent_slot_child",
            "parent_object_id",
            "slot_name",
            "child_object_id",
        ),
    )

    parent_object_id: Mapped[str] = mapped_column(Text, nullable=False)
    slot_name: Mapped[str] = mapped_column(Text, nullable=False)
    child_object_id: Mapped[str] = mapped_column(Text, primary_key=True)

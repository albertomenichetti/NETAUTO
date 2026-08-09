"""SQLAlchemy row models for datatype and object template persistence."""

from sqlalchemy import Boolean, ForeignKey, PrimaryKeyConstraint, Text, UniqueConstraint
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
    properties_json: Mapped[str] = mapped_column(Text, nullable=False)

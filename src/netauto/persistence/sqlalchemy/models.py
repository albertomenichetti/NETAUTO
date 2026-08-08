"""SQLAlchemy row models for datatype persistence."""

from sqlalchemy import ForeignKey, PrimaryKeyConstraint, Text, UniqueConstraint
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

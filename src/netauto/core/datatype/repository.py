"""Persistence-neutral repository contract for datatypes."""

from typing import Protocol
from uuid import UUID

from netauto.core.datatype.models import DataType, DataTypeVersion


class DataTypeRepository(Protocol):
    """Repository contract for datatype persistence."""

    def add(self, datatype: DataType) -> None:
        """Persist a new datatype identity."""
        ...

    def get(self, datatype_id: UUID) -> DataType | None:
        """Return a datatype by UUID or None."""
        ...

    def get_by_name(self, namespace: str, name: str) -> DataType | None:
        """Return a datatype by logical name or None."""
        ...

    def add_version(self, version: DataTypeVersion) -> None:
        """Persist a new datatype version snapshot."""
        ...

    def get_version(self, datatype_id: UUID, version: int) -> DataTypeVersion | None:
        """Return an exact datatype version or None."""
        ...

    def list_versions(self, datatype_id: UUID) -> tuple[DataTypeVersion, ...]:
        """Return all versions ordered by version ascending."""
        ...

    def replace_version(self, version: DataTypeVersion) -> None:
        """Replace an existing datatype version snapshot."""
        ...

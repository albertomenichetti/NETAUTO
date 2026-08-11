"""Persistence-neutral repository contract and guards for datatypes."""

from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from netauto.core.datatype.exceptions import DataTypePersistenceError
from netauto.core.datatype.models import DataType, DataTypeVersion, DataTypeVersionStatus


class DataTypeRepository(Protocol):
    """Repository contract for datatype persistence.

    Repositories enforce the persisted DataTypeVersion lifecycle contract:

    - new persisted versions must enter as DRAFT
    - DRAFT -> DRAFT may revise constraints only
    - DRAFT -> PUBLISHED is a status-only transition
    - PUBLISHED -> DEPRECATED is a status-only transition
    - DEPRECATED is terminal
    - base_type is stable across the full datatype lineage
    """

    def list(self) -> tuple[DataType, ...]:
        """Return all datatypes ordered deterministically."""
        ...

    def add(self, datatype: DataType) -> None:
        """Persist a new datatype identity."""
        ...

    def get(self, datatype_id: UUID) -> DataType | None:
        """Return a datatype by UUID or None."""
        ...

    def get_by_name(self, namespace: str, name: str) -> DataType | None:
        """Return a datatype by logical name or None."""
        ...

    def delete(self, datatype_id: UUID) -> None:
        """Delete a datatype identity and all of its versions."""
        ...

    def add_version(self, version: DataTypeVersion) -> None:
        """Persist a new datatype version snapshot as a new DRAFT only."""
        ...

    def get_version(self, datatype_id: UUID, version: int) -> DataTypeVersion | None:
        """Return an exact datatype version or None."""
        ...

    def list_versions(self, datatype_id: UUID) -> tuple[DataTypeVersion, ...]:
        """Return all versions ordered by version ascending."""
        ...

    def replace_version(self, version: DataTypeVersion) -> None:
        """Replace an existing datatype version using the constrained lifecycle rules."""
        ...


def validate_datatype_version_add(
    version: DataTypeVersion,
    *,
    existing_versions: Iterable[DataTypeVersion],
) -> None:
    """Validate that a new persisted version satisfies repository invariants."""
    if version.status is not DataTypeVersionStatus.DRAFT:
        raise DataTypePersistenceError("New datatype versions must be persisted as draft.")

    lineage_base_type: str | None = None
    for existing in existing_versions:
        if existing.datatype_id != version.datatype_id:
            raise DataTypePersistenceError("Stored datatype lineage is corrupt.")
        existing_base_type = existing.base_type.name
        if lineage_base_type is None:
            lineage_base_type = existing_base_type
            continue
        if existing_base_type != lineage_base_type:
            raise DataTypePersistenceError("Stored datatype lineage has inconsistent base types.")

    if lineage_base_type is not None and version.base_type.name != lineage_base_type:
        raise DataTypePersistenceError("Datatype base_type is immutable across the lineage.")


def validate_datatype_version_replace(
    current: DataTypeVersion,
    replacement: DataTypeVersion,
) -> None:
    """Validate that an exact persisted version replacement is legal."""
    if (
        replacement.datatype_id != current.datatype_id
        or replacement.version != current.version
    ):
        raise DataTypePersistenceError("Datatype version identity is immutable.")

    if replacement.base_type.name != current.base_type.name:
        raise DataTypePersistenceError("Datatype base_type is immutable across the lineage.")

    current_status = current.status
    replacement_status = replacement.status

    if current_status is DataTypeVersionStatus.DRAFT:
        if replacement_status is DataTypeVersionStatus.DRAFT:
            return
        if replacement_status is DataTypeVersionStatus.PUBLISHED:
            if replacement.constraints != current.constraints:
                raise DataTypePersistenceError(
                    "Publishing a datatype version may not change its schema snapshot."
                )
            return
        raise DataTypePersistenceError("Draft datatype versions may only be revised or published.")

    if current_status is DataTypeVersionStatus.PUBLISHED:
        if replacement_status is DataTypeVersionStatus.DEPRECATED:
            if replacement.constraints != current.constraints:
                raise DataTypePersistenceError(
                    "Deprecating a datatype version may not change its schema snapshot."
                )
            return
        raise DataTypePersistenceError(
            "Published datatype versions may only transition to deprecated."
        )

    raise DataTypePersistenceError("Deprecated datatype versions are terminal.")

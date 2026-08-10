"""Lifecycle and version creation operations for datatype versions."""

from collections.abc import Iterable

from netauto.core.datatype.compiler import SchemaCompiler
from netauto.core.datatype.constraints import Constraint
from netauto.core.datatype.exceptions import (
    InvalidDataTypeVersionTransition,
    MismatchedDataTypeVersion,
)
from netauto.core.datatype.models import DataTypeVersion, DataTypeVersionStatus


class DataTypeVersioningService:
    """Operate on immutable datatype version snapshots."""

    def __init__(self) -> None:
        self._compiler = SchemaCompiler()

    def revise_draft(
        self,
        version: DataTypeVersion,
        *,
        constraints: Iterable[Constraint],
    ) -> DataTypeVersion:
        if version.status is not DataTypeVersionStatus.DRAFT:
            raise InvalidDataTypeVersionTransition("Only draft versions may be revised.")
        return DataTypeVersion(
            datatype_id=version.datatype_id,
            version=version.version,
            status=DataTypeVersionStatus.DRAFT,
            base_type=version.base_type,
            constraints=tuple(constraints),
        )

    def publish(self, version: DataTypeVersion) -> DataTypeVersion:
        if version.status is not DataTypeVersionStatus.DRAFT:
            raise InvalidDataTypeVersionTransition("Only draft versions may be published.")
        self._compiler.compile_datatype(version)
        return DataTypeVersion(
            datatype_id=version.datatype_id,
            version=version.version,
            status=DataTypeVersionStatus.PUBLISHED,
            base_type=version.base_type,
            constraints=version.constraints,
        )

    def deprecate(self, version: DataTypeVersion) -> DataTypeVersion:
        if version.status is not DataTypeVersionStatus.PUBLISHED:
            raise InvalidDataTypeVersionTransition("Only published versions may be deprecated.")
        return DataTypeVersion(
            datatype_id=version.datatype_id,
            version=version.version,
            status=DataTypeVersionStatus.DEPRECATED,
            base_type=version.base_type,
            constraints=version.constraints,
        )

    def create_next_version(
        self,
        source: DataTypeVersion,
        *,
        existing_versions: Iterable[DataTypeVersion],
    ) -> DataTypeVersion:
        if source.status not in (
            DataTypeVersionStatus.PUBLISHED,
            DataTypeVersionStatus.DEPRECATED,
        ):
            raise InvalidDataTypeVersionTransition(
                "Only published or deprecated versions may be used to create the next version."
            )

        versions = tuple(existing_versions)
        version_numbers = [source.version]
        for candidate in versions:
            if candidate.datatype_id != source.datatype_id:
                raise MismatchedDataTypeVersion(
                    "All existing versions must belong to the same datatype."
                )
            version_numbers.append(candidate.version)

        return DataTypeVersion(
            datatype_id=source.datatype_id,
            version=max(version_numbers) + 1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=source.base_type,
            constraints=source.constraints,
        )

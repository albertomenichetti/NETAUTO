"""Application service for datatype workflows."""

from collections.abc import Iterable
from uuid import UUID

from netauto.application.unit_of_work import DataTypeUnitOfWorkFactory
from netauto.core.datatype import (
    Constraint,
    DataType,
    DataTypeFactory,
    DataTypeInUse,
    DataTypeNotFound,
    DataTypeVersion,
    DataTypeVersioningService,
    DataTypeVersionNotFound,
)


class DataTypeApplicationService:
    """Orchestrate datatype use cases over a unit of work boundary."""

    def __init__(self, uow_factory: DataTypeUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory
        self._factory = DataTypeFactory()
        self._versioning = DataTypeVersioningService()

    def create_datatype(
        self,
        *,
        namespace: str,
        name: str,
        description: str | None,
        base_type: str,
        constraints: Iterable[Constraint],
    ) -> tuple[DataType, DataTypeVersion]:
        datatype, version = self._factory.create(
            namespace=namespace,
            name=name,
            description=description,
            base_type=base_type,
            constraints=constraints,
        )
        with self._uow_factory() as uow:
            uow.datatypes.add(datatype)
            uow.datatypes.add_version(version)
            uow.commit()
        return datatype, version

    def list_datatypes(self) -> tuple[DataType, ...]:
        with self._uow_factory() as uow:
            return uow.datatypes.list()

    def get_datatype(self, datatype_id: UUID) -> DataType:
        with self._uow_factory() as uow:
            datatype = uow.datatypes.get(datatype_id)
            if datatype is None:
                raise DataTypeNotFound("Datatype does not exist.")
            return datatype

    def get_datatype_by_name(self, namespace: str, name: str) -> DataType:
        with self._uow_factory() as uow:
            datatype = uow.datatypes.get_by_name(namespace, name)
            if datatype is None:
                raise DataTypeNotFound("Datatype does not exist.")
            return datatype

    def list_versions(self, datatype_id: UUID) -> tuple[DataTypeVersion, ...]:
        with self._uow_factory() as uow:
            datatype = uow.datatypes.get(datatype_id)
            if datatype is None:
                raise DataTypeNotFound("Datatype does not exist.")
            return uow.datatypes.list_versions(datatype_id)

    def get_version(self, datatype_id: UUID, version: int) -> DataTypeVersion:
        with self._uow_factory() as uow:
            datatype = uow.datatypes.get(datatype_id)
            if datatype is None:
                raise DataTypeNotFound("Datatype does not exist.")
            loaded = uow.datatypes.get_version(datatype_id, version)
            if loaded is None:
                raise DataTypeVersionNotFound("Datatype version does not exist.")
            return loaded

    def revise_version(
        self,
        *,
        datatype_id: UUID,
        version: int,
        constraints: Iterable[Constraint],
    ) -> DataTypeVersion:
        with self._uow_factory() as uow:
            datatype = uow.datatypes.get(datatype_id)
            if datatype is None:
                raise DataTypeNotFound("Datatype does not exist.")
            current = uow.datatypes.get_version(datatype_id, version)
            if current is None:
                raise DataTypeVersionNotFound("Datatype version does not exist.")
            revised = self._versioning.revise_draft(
                current,
                constraints=constraints,
            )
            uow.datatypes.replace_version(revised)
            uow.commit()
            return revised

    def create_next_version(
        self,
        *,
        datatype_id: UUID,
        source_version: int,
    ) -> DataTypeVersion:
        with self._uow_factory() as uow:
            datatype = uow.datatypes.get(datatype_id)
            if datatype is None:
                raise DataTypeNotFound("Datatype does not exist.")
            source = uow.datatypes.get_version(datatype_id, source_version)
            if source is None:
                raise DataTypeVersionNotFound("Datatype version does not exist.")
            existing_versions = uow.datatypes.list_versions(datatype_id)
            next_version = self._versioning.create_next_version(
                source,
                existing_versions=existing_versions,
            )
            uow.datatypes.add_version(next_version)
            uow.commit()
            return next_version

    def publish_version(self, *, datatype_id: UUID, version: int) -> DataTypeVersion:
        with self._uow_factory() as uow:
            datatype = uow.datatypes.get(datatype_id)
            if datatype is None:
                raise DataTypeNotFound("Datatype does not exist.")
            current = uow.datatypes.get_version(datatype_id, version)
            if current is None:
                raise DataTypeVersionNotFound("Datatype version does not exist.")
            published = self._versioning.publish(current)
            uow.datatypes.replace_version(published)
            uow.commit()
            return published

    def deprecate_version(self, *, datatype_id: UUID, version: int) -> DataTypeVersion:
        with self._uow_factory() as uow:
            datatype = uow.datatypes.get(datatype_id)
            if datatype is None:
                raise DataTypeNotFound("Datatype does not exist.")
            current = uow.datatypes.get_version(datatype_id, version)
            if current is None:
                raise DataTypeVersionNotFound("Datatype version does not exist.")
            deprecated = self._versioning.deprecate(current)
            uow.datatypes.replace_version(deprecated)
            uow.commit()
            return deprecated

    def delete_datatype(self, datatype_id: UUID) -> None:
        with self._uow_factory() as uow:
            datatype = uow.datatypes.get(datatype_id)
            if datatype is None:
                raise DataTypeNotFound("Datatype does not exist.")

            for template in uow.object_templates.list():
                for version in uow.object_templates.list_versions(template.id):
                    for property_definition in version.properties:
                        if property_definition.datatype_id == datatype_id:
                            raise DataTypeInUse(
                                "Datatype is still referenced by an object template."
                            )

            uow.datatypes.delete(datatype_id)
            uow.commit()

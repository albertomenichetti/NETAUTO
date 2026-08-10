"""In-memory datatype repository implementation."""

from uuid import UUID

from netauto.core.datatype import (
    DataType,
    DataTypeAlreadyExists,
    DataTypeNotFound,
    DataTypeRepository,
    DataTypeVersion,
    DataTypeVersionAlreadyExists,
    DataTypeVersionNotFound,
)


class InMemoryDataTypeRepository(DataTypeRepository):
    """Reference in-memory datatype repository."""

    def __init__(self) -> None:
        self._datatypes: dict[UUID, DataType] = {}
        self._datatype_names: dict[tuple[str, str], UUID] = {}
        self._versions: dict[tuple[UUID, int], DataTypeVersion] = {}

    def list(self) -> tuple[DataType, ...]:
        datatypes = list(self._datatypes.values())
        datatypes.sort(key=lambda item: (item.namespace, item.name, str(item.id)))
        return tuple(datatypes)

    def add(self, datatype: DataType) -> None:
        if datatype.id in self._datatypes:
            raise DataTypeAlreadyExists("Datatype UUID already exists.")
        name_key = (datatype.namespace, datatype.name)
        if name_key in self._datatype_names:
            raise DataTypeAlreadyExists("Datatype logical name already exists.")
        self._datatypes[datatype.id] = datatype
        self._datatype_names[name_key] = datatype.id

    def get(self, datatype_id: UUID) -> DataType | None:
        return self._datatypes.get(datatype_id)

    def get_by_name(self, namespace: str, name: str) -> DataType | None:
        datatype_id = self._datatype_names.get((namespace, name))
        if datatype_id is None:
            return None
        return self._datatypes[datatype_id]

    def delete(self, datatype_id: UUID) -> None:
        datatype = self._datatypes.get(datatype_id)
        if datatype is None:
            raise DataTypeNotFound("Datatype does not exist.")
        del self._datatypes[datatype_id]
        del self._datatype_names[(datatype.namespace, datatype.name)]
        version_keys = [
            version_key
            for version_key in self._versions
            if version_key[0] == datatype_id
        ]
        for version_key in version_keys:
            del self._versions[version_key]

    def add_version(self, version: DataTypeVersion) -> None:
        if version.datatype_id not in self._datatypes:
            raise DataTypeNotFound("Parent datatype does not exist.")
        version_key = (version.datatype_id, version.version)
        if version_key in self._versions:
            raise DataTypeVersionAlreadyExists("Datatype version already exists.")
        self._versions[version_key] = version

    def get_version(self, datatype_id: UUID, version: int) -> DataTypeVersion | None:
        return self._versions.get((datatype_id, version))

    def list_versions(self, datatype_id: UUID) -> tuple[DataTypeVersion, ...]:
        versions = [
            version
            for (candidate_datatype_id, _), version in self._versions.items()
            if candidate_datatype_id == datatype_id
        ]
        versions.sort(key=lambda item: item.version)
        return tuple(versions)

    def replace_version(self, version: DataTypeVersion) -> None:
        version_key = (version.datatype_id, version.version)
        if version_key not in self._versions:
            raise DataTypeVersionNotFound("Datatype version does not exist.")
        self._versions[version_key] = version

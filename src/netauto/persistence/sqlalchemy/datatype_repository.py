"""SQLAlchemy datatype repository implementation."""

import json
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataType,
    DataTypeAlreadyExists,
    DataTypeNotFound,
    DataTypePersistenceError,
    DataTypeRepository,
    DataTypeVersion,
    DataTypeVersionAlreadyExists,
    DataTypeVersionNotFound,
    DataTypeVersionStatus,
    PrimitiveTypeNotFound,
    PrimitiveTypeRegistry,
)
from netauto.persistence.sqlalchemy.models import DataTypeRow, DataTypeVersionRow


def _serialize_constraints(constraints: tuple[Constraint, ...]) -> str:
    payload: list[dict[str, object]] = []
    for constraint in constraints:
        value = constraint.value
        if constraint.name is ConstraintName.ENUM:
            value = list(cast("tuple[object, ...]", value))
        payload.append({"name": constraint.name.value, "value": value})
    return json.dumps(payload, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _deserialize_constraints(constraints_json: str) -> tuple[Constraint, ...]:
    try:
        payload = json.loads(constraints_json)
    except json.JSONDecodeError as error:
        raise DataTypePersistenceError("Stored constraint JSON is invalid.") from error
    if not isinstance(payload, list):
        raise DataTypePersistenceError("Stored constraints must be a JSON array.")

    constraints: list[Constraint] = []
    for item in payload:
        if not isinstance(item, dict):
            raise DataTypePersistenceError("Stored constraint entry must be a JSON object.")
        if set(item.keys()) != {"name", "value"}:
            raise DataTypePersistenceError("Stored constraint entry must contain name and value.")
        try:
            name = ConstraintName(item["name"])
        except Exception as error:
            raise DataTypePersistenceError("Stored constraint name is invalid.") from error
        constraints.append(Constraint(name=name, value=item["value"]))
    return tuple(constraints)


def _row_to_datatype(row: DataTypeRow) -> DataType:
    try:
        return DataType(
            id=UUID(row.id),
            namespace=row.namespace,
            name=row.name,
            description=row.description,
        )
    except Exception as error:
        raise DataTypePersistenceError("Stored datatype row is invalid.") from error


def _row_to_version(
    row: DataTypeVersionRow,
    primitive_registry: PrimitiveTypeRegistry,
) -> DataTypeVersion:
    try:
        status = DataTypeVersionStatus(row.status)
        primitive = primitive_registry.get(row.base_type)
        constraints = _deserialize_constraints(row.constraints_json)
        return DataTypeVersion(
            datatype_id=UUID(row.datatype_id),
            version=row.version,
            status=status,
            base_type=primitive,
            constraints=constraints,
        )
    except PrimitiveTypeNotFound as error:
        raise DataTypePersistenceError("Stored datatype version row is invalid.") from error
    except DataTypePersistenceError:
        raise
    except Exception as error:
        raise DataTypePersistenceError("Stored datatype version row is invalid.") from error


class SqlAlchemyDataTypeRepository(DataTypeRepository):
    """SQLAlchemy-backed datatype repository."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._primitive_registry = PrimitiveTypeRegistry()

    def add(self, datatype: DataType) -> None:
        self._session.add(
            DataTypeRow(
                id=str(datatype.id),
                namespace=datatype.namespace,
                name=datatype.name,
                description=datatype.description,
            )
        )
        try:
            self._session.flush()
        except IntegrityError as error:
            raise DataTypeAlreadyExists("Datatype UUID or logical name already exists.") from error

    def get(self, datatype_id: UUID) -> DataType | None:
        row = self._session.get(DataTypeRow, str(datatype_id))
        if row is None:
            return None
        return _row_to_datatype(row)

    def get_by_name(self, namespace: str, name: str) -> DataType | None:
        row = self._session.scalar(
            select(DataTypeRow).where(
                DataTypeRow.namespace == namespace,
                DataTypeRow.name == name,
            )
        )
        if row is None:
            return None
        return _row_to_datatype(row)

    def add_version(self, version: DataTypeVersion) -> None:
        parent = self._session.get(DataTypeRow, str(version.datatype_id))
        if parent is None:
            raise DataTypeNotFound("Parent datatype does not exist.")
        self._session.add(
            DataTypeVersionRow(
                datatype_id=str(version.datatype_id),
                version=version.version,
                status=version.status.value,
                base_type=version.base_type.name,
                constraints_json=_serialize_constraints(version.constraints),
            )
        )
        try:
            self._session.flush()
        except IntegrityError as error:
            raise DataTypeVersionAlreadyExists("Datatype version already exists.") from error

    def get_version(self, datatype_id: UUID, version: int) -> DataTypeVersion | None:
        row = self._session.get(
            DataTypeVersionRow,
            {"datatype_id": str(datatype_id), "version": version},
        )
        if row is None:
            return None
        return _row_to_version(row, self._primitive_registry)

    def list_versions(self, datatype_id: UUID) -> tuple[DataTypeVersion, ...]:
        rows = self._session.scalars(
            select(DataTypeVersionRow)
            .where(DataTypeVersionRow.datatype_id == str(datatype_id))
            .order_by(DataTypeVersionRow.version.asc())
        ).all()
        return tuple(_row_to_version(row, self._primitive_registry) for row in rows)

    def replace_version(self, version: DataTypeVersion) -> None:
        row = self._session.get(
            DataTypeVersionRow,
            {"datatype_id": str(version.datatype_id), "version": version.version},
        )
        if row is None:
            raise DataTypeVersionNotFound("Datatype version does not exist.")
        row.status = version.status.value
        row.base_type = version.base_type.name
        row.constraints_json = _serialize_constraints(version.constraints)
        try:
            self._session.flush()
        except IntegrityError as error:
            raise DataTypePersistenceError("Datatype version replacement failed.") from error

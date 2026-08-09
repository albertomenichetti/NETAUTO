"""SQLAlchemy object repository implementation."""

import json
from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from netauto.core.object import (
    ComponentMembership,
    ComponentMembershipAlreadyExists,
    ComponentMembershipNotFound,
    Object,
    ObjectAlreadyExists,
    ObjectNotFound,
    ObjectPersistenceError,
    ObjectRepository,
)
from netauto.persistence.sqlalchemy.models import ObjectComponentRow, ObjectRow


def _serialize_properties(properties: Mapping[str, object]) -> str:
    try:
        return json.dumps(
            dict(properties),
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except Exception as error:
        raise ObjectPersistenceError(
            "Object properties could not be serialized to JSON."
        ) from error


def _row_to_object(row: ObjectRow) -> Object:
    try:
        payload = json.loads(row.properties_json)
    except json.JSONDecodeError as error:
        raise ObjectPersistenceError("Stored object properties JSON is invalid.") from error
    if not isinstance(payload, dict):
        raise ObjectPersistenceError("Stored object properties must be a JSON object.")

    try:
        return Object(
            id=UUID(row.id),
            template_id=UUID(row.template_id),
            template_version=row.template_version,
            properties=payload,
        )
    except Exception as error:
        raise ObjectPersistenceError("Stored object row is invalid.") from error


def _row_to_membership(row: ObjectComponentRow) -> ComponentMembership:
    try:
        return ComponentMembership(
            parent_object_id=UUID(row.parent_object_id),
            slot_name=row.slot_name,
            child_object_id=UUID(row.child_object_id),
        )
    except Exception as error:
        raise ObjectPersistenceError("Stored component membership row is invalid.") from error


class SqlAlchemyObjectRepository(ObjectRepository):
    """SQLAlchemy-backed object repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self) -> tuple[Object, ...]:
        rows = self._session.scalars(select(ObjectRow).order_by(ObjectRow.id.asc())).all()
        return tuple(_row_to_object(row) for row in rows)

    def add(self, object_value: Object) -> None:
        self._session.add(
            ObjectRow(
                id=str(object_value.id),
                template_id=str(object_value.template_id),
                template_version=object_value.template_version,
                properties_json=_serialize_properties(object_value.properties),
            )
        )
        try:
            self._session.flush()
        except IntegrityError as error:
            raise ObjectAlreadyExists("Object UUID already exists.") from error

    def get(self, object_id: UUID) -> Object | None:
        row = self._session.get(ObjectRow, str(object_id))
        if row is None:
            return None
        return _row_to_object(row)

    def replace(self, object_value: Object) -> None:
        row = self._session.get(ObjectRow, str(object_value.id))
        if row is None:
            raise ObjectNotFound("Object does not exist.")
        row.template_id = str(object_value.template_id)
        row.template_version = object_value.template_version
        row.properties_json = _serialize_properties(object_value.properties)
        self._session.flush()

    def delete(self, object_id: UUID) -> None:
        row = self._session.get(ObjectRow, str(object_id))
        if row is None:
            raise ObjectNotFound("Object does not exist.")
        self._session.delete(row)
        self._session.flush()

    def add_membership(self, membership: ComponentMembership) -> None:
        if self._session.get(ObjectRow, str(membership.parent_object_id)) is None:
            raise ObjectNotFound("Object does not exist.")
        if self._session.get(ObjectRow, str(membership.child_object_id)) is None:
            raise ObjectNotFound("Object does not exist.")
        self._session.add(
            ObjectComponentRow(
                parent_object_id=str(membership.parent_object_id),
                slot_name=membership.slot_name,
                child_object_id=str(membership.child_object_id),
            )
        )
        try:
            self._session.flush()
        except IntegrityError as error:
            raise ComponentMembershipAlreadyExists(
                "Component membership for child object already exists."
            ) from error

    def get_owner(self, child_object_id: UUID) -> ComponentMembership | None:
        row = self._session.get(ObjectComponentRow, str(child_object_id))
        if row is None:
            return None
        return _row_to_membership(row)

    def list_components(
        self,
        parent_object_id: UUID,
        slot_name: str | None = None,
    ) -> tuple[ComponentMembership, ...]:
        query = select(ObjectComponentRow).where(
            ObjectComponentRow.parent_object_id == str(parent_object_id)
        )
        if slot_name is not None:
            query = query.where(ObjectComponentRow.slot_name == slot_name)
        rows = self._session.scalars(
            query.order_by(
                ObjectComponentRow.slot_name.asc(),
                ObjectComponentRow.child_object_id.asc(),
            )
        ).all()
        return tuple(_row_to_membership(row) for row in rows)

    def remove_membership(self, child_object_id: UUID) -> None:
        row = self._session.get(ObjectComponentRow, str(child_object_id))
        if row is None:
            raise ComponentMembershipNotFound("Component membership does not exist.")
        self._session.delete(row)
        self._session.flush()

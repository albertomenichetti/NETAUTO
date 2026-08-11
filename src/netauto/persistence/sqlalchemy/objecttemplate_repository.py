"""SQLAlchemy object template repository implementation."""

import json
from collections import defaultdict
from uuid import UUID

from sqlalchemy import delete, select, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateAlreadyExists,
    ObjectTemplateComponent,
    ObjectTemplateNotFound,
    ObjectTemplatePersistenceError,
    ObjectTemplateProperty,
    ObjectTemplateRepository,
    ObjectTemplateVersion,
    ObjectTemplateVersionAlreadyExists,
    ObjectTemplateVersionNotFound,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.persistence.sqlalchemy.models import (
    ObjectRow,
    ObjectTemplatePropertyRow,
    ObjectTemplateRow,
    ObjectTemplateVersionRow,
    RelationshipDefinitionRow,
)


def _serialize_components(components: tuple[ObjectTemplateComponent, ...]) -> str:
    payload = [
        {
            "name": component.name,
            "template_id": str(component.template_id),
        }
        for component in components
    ]
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _deserialize_components(components_json: str) -> tuple[ObjectTemplateComponent, ...]:
    try:
        payload = json.loads(components_json)
    except json.JSONDecodeError as error:
        raise ObjectTemplatePersistenceError(
            "Stored object template component JSON is invalid."
        ) from error
    if not isinstance(payload, list):
        raise ObjectTemplatePersistenceError(
            "Stored object template components must be a JSON array."
        )

    components: list[ObjectTemplateComponent] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ObjectTemplatePersistenceError(
                "Stored object template component entry must be a JSON object."
            )
        if set(item.keys()) not in (
            {"name", "template_id"},
            {"name", "template_id", "template_version"},
        ):
            raise ObjectTemplatePersistenceError(
                "Stored object template component entry has an invalid shape."
            )
        try:
            components.append(
                ObjectTemplateComponent(
                    name=item["name"],
                    template_id=UUID(item["template_id"]),
                )
            )
        except Exception as error:
            raise ObjectTemplatePersistenceError(
                "Stored object template component entry is invalid."
            ) from error
    return tuple(components)


def _row_to_object_template(row: ObjectTemplateRow) -> ObjectTemplate:
    try:
        return ObjectTemplate(
            id=UUID(row.id),
            namespace=row.namespace,
            name=row.name,
            description=row.description,
            abstract=row.abstract,
        )
    except Exception as error:
        raise ObjectTemplatePersistenceError("Stored object template row is invalid.") from error


def _row_to_object_template_property(row: ObjectTemplatePropertyRow) -> ObjectTemplateProperty:
    try:
        return ObjectTemplateProperty(
            name=row.name,
            datatype_id=UUID(row.datatype_id),
            datatype_version=row.datatype_version,
            required=row.required,
        )
    except Exception as error:
        raise ObjectTemplatePersistenceError(
            "Stored object template property row is invalid."
        ) from error


def _row_to_object_template_version(
    row: ObjectTemplateVersionRow,
    property_rows: tuple[ObjectTemplatePropertyRow, ...],
) -> ObjectTemplateVersion:
    try:
        if row.parent_template_id is None and row.parent_version is None:
            parent = None
        elif row.parent_template_id is not None and row.parent_version is not None:
            parent = ObjectTemplateVersionRef(
                template_id=UUID(row.parent_template_id),
                version=row.parent_version,
            )
        else:
            raise ObjectTemplatePersistenceError(
                "Stored object template version parent reference has an invalid shape."
            )

        return ObjectTemplateVersion(
            template_id=UUID(row.template_id),
            version=row.version,
            status=ObjectTemplateVersionStatus(row.status),
            parent=parent,
            properties=tuple(_row_to_object_template_property(prop) for prop in property_rows),
            components=_deserialize_components(row.components_json),
        )
    except ObjectTemplatePersistenceError:
        raise
    except Exception as error:
        raise ObjectTemplatePersistenceError(
            "Stored object template version row is invalid."
        ) from error


class SqlAlchemyObjectTemplateRepository(ObjectTemplateRepository):
    """SQLAlchemy-backed object template repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self) -> tuple[ObjectTemplate, ...]:
        rows = self._session.scalars(
            select(ObjectTemplateRow).order_by(
                ObjectTemplateRow.namespace.asc(),
                ObjectTemplateRow.name.asc(),
                ObjectTemplateRow.id.asc(),
            )
        ).all()
        return tuple(_row_to_object_template(row) for row in rows)

    def add(self, template: ObjectTemplate) -> None:
        self._session.add(
            ObjectTemplateRow(
                id=str(template.id),
                namespace=template.namespace,
                name=template.name,
                description=template.description,
                abstract=template.abstract,
            )
        )
        try:
            self._session.flush()
        except IntegrityError as error:
            raise ObjectTemplateAlreadyExists(
                "ObjectTemplate UUID or logical name already exists."
            ) from error

    def get(self, template_id: UUID) -> ObjectTemplate | None:
        row = self._session.get(ObjectTemplateRow, str(template_id))
        if row is None:
            return None
        return _row_to_object_template(row)

    def get_by_name(self, namespace: str, name: str) -> ObjectTemplate | None:
        row = self._session.scalar(
            select(ObjectTemplateRow).where(
                ObjectTemplateRow.namespace == namespace,
                ObjectTemplateRow.name == name,
            )
        )
        if row is None:
            return None
        return _row_to_object_template(row)

    def _assert_delete_dependencies_absent(self, template_id: UUID) -> None:
        template_id_text = str(template_id)

        object_reference = self._session.scalar(
            select(ObjectRow.id)
            .where(ObjectRow.template_id == template_id_text)
            .limit(1)
        )
        if object_reference is not None:
            raise ObjectTemplatePersistenceError(
                "ObjectTemplate deletion blocked by a persisted object reference."
            )

        inherited_reference = self._session.scalar(
            select(ObjectTemplateVersionRow.template_id)
            .where(
                ObjectTemplateVersionRow.template_id != template_id_text,
                ObjectTemplateVersionRow.parent_template_id == template_id_text,
            )
            .limit(1)
        )
        if inherited_reference is not None:
            raise ObjectTemplatePersistenceError(
                "ObjectTemplate deletion blocked by a persisted inheritance reference."
            )

        component_rows = self._session.scalars(
            select(ObjectTemplateVersionRow).where(
                ObjectTemplateVersionRow.template_id != template_id_text,
            )
        ).all()
        for row in component_rows:
            components = _deserialize_components(row.components_json)
            if any(component.template_id == template_id for component in components):
                raise ObjectTemplatePersistenceError(
                    "ObjectTemplate deletion blocked by a persisted component reference."
                )

        relationship_reference = self._session.scalar(
            select(RelationshipDefinitionRow.id)
            .where(
                (RelationshipDefinitionRow.source_template_id == template_id_text)
                | (RelationshipDefinitionRow.target_template_id == template_id_text)
            )
            .limit(1)
        )
        if relationship_reference is not None:
            raise ObjectTemplatePersistenceError(
                "ObjectTemplate deletion blocked by a persisted relationship-definition "
                "reference."
            )

    def delete(self, template_id: UUID) -> None:
        owner = self._session.get(ObjectTemplateRow, str(template_id))
        if owner is None:
            raise ObjectTemplateNotFound("ObjectTemplate does not exist.")
        self._assert_delete_dependencies_absent(template_id)
        self._session.execute(
            delete(ObjectTemplateVersionRow).where(
                ObjectTemplateVersionRow.template_id == str(template_id)
            )
        )
        self._session.delete(owner)
        try:
            self._session.flush()
        except IntegrityError as error:
            raise ObjectTemplatePersistenceError(
                "ObjectTemplate deletion failed."
            ) from error

    def _property_rows_for_version(
        self,
        template_id: UUID,
        version: int,
    ) -> tuple[ObjectTemplatePropertyRow, ...]:
        rows = self._session.scalars(
            select(ObjectTemplatePropertyRow)
            .where(
                ObjectTemplatePropertyRow.template_id == str(template_id),
                ObjectTemplatePropertyRow.template_version == version,
            )
            .order_by(ObjectTemplatePropertyRow.position.asc())
        ).all()
        return tuple(rows)

    def _property_rows_for_versions(
        self,
        rows: tuple[ObjectTemplateVersionRow, ...],
    ) -> dict[tuple[str, int], tuple[ObjectTemplatePropertyRow, ...]]:
        if not rows:
            return {}

        owner_keys = [(row.template_id, row.version) for row in rows]
        property_rows = self._session.scalars(
            select(ObjectTemplatePropertyRow)
            .where(
                tuple_(
                    ObjectTemplatePropertyRow.template_id,
                    ObjectTemplatePropertyRow.template_version,
                ).in_(owner_keys)
            )
            .order_by(
                ObjectTemplatePropertyRow.template_id.asc(),
                ObjectTemplatePropertyRow.template_version.asc(),
                ObjectTemplatePropertyRow.position.asc(),
            )
        ).all()
        grouped: defaultdict[tuple[str, int], list[ObjectTemplatePropertyRow]] = defaultdict(list)
        for row in property_rows:
            grouped[(row.template_id, row.template_version)].append(row)
        return {key: tuple(value) for key, value in grouped.items()}

    def _add_property_rows(self, version: ObjectTemplateVersion) -> None:
        for position, prop in enumerate(version.properties):
            self._session.add(
                ObjectTemplatePropertyRow(
                    template_id=str(version.template_id),
                    template_version=version.version,
                    position=position,
                    name=prop.name,
                    datatype_id=str(prop.datatype_id),
                    datatype_version=prop.datatype_version,
                    required=prop.required,
                )
            )

    def add_version(self, version: ObjectTemplateVersion) -> None:
        owner = self._session.get(ObjectTemplateRow, str(version.template_id))
        if owner is None:
            raise ObjectTemplateNotFound("Owning object template does not exist.")
        existing = self._session.get(
            ObjectTemplateVersionRow,
            {"template_id": str(version.template_id), "version": version.version},
        )
        if existing is not None:
            raise ObjectTemplateVersionAlreadyExists("ObjectTemplate version already exists.")
        self._session.add(
            ObjectTemplateVersionRow(
                template_id=str(version.template_id),
                version=version.version,
                status=version.status.value,
                parent_template_id=(
                    str(version.parent.template_id) if version.parent is not None else None
                ),
                parent_version=version.parent.version if version.parent is not None else None,
                components_json=_serialize_components(version.components),
            )
        )
        try:
            self._session.flush()
            self._add_property_rows(version)
            self._session.flush()
        except IntegrityError as error:
            raise ObjectTemplatePersistenceError(
                "ObjectTemplate version persistence failed."
            ) from error

    def get_version(self, template_id: UUID, version: int) -> ObjectTemplateVersion | None:
        row = self._session.get(
            ObjectTemplateVersionRow,
            {"template_id": str(template_id), "version": version},
        )
        if row is None:
            return None
        return _row_to_object_template_version(
            row,
            self._property_rows_for_version(template_id, version),
        )

    def list_versions(self, template_id: UUID) -> tuple[ObjectTemplateVersion, ...]:
        rows = tuple(
            self._session.scalars(
                select(ObjectTemplateVersionRow)
                .where(ObjectTemplateVersionRow.template_id == str(template_id))
                .order_by(ObjectTemplateVersionRow.version.asc())
            ).all()
        )
        property_rows = self._property_rows_for_versions(rows)
        return tuple(
            _row_to_object_template_version(
                row,
                property_rows.get((row.template_id, row.version), ()),
            )
            for row in rows
        )

    def replace_version(self, version: ObjectTemplateVersion) -> None:
        row = self._session.get(
            ObjectTemplateVersionRow,
            {"template_id": str(version.template_id), "version": version.version},
        )
        if row is None:
            raise ObjectTemplateVersionNotFound("ObjectTemplate version does not exist.")
        row.status = version.status.value
        row.parent_template_id = (
            str(version.parent.template_id) if version.parent is not None else None
        )
        row.parent_version = version.parent.version if version.parent is not None else None
        row.components_json = _serialize_components(version.components)
        self._session.execute(
            delete(ObjectTemplatePropertyRow).where(
                ObjectTemplatePropertyRow.template_id == str(version.template_id),
                ObjectTemplatePropertyRow.template_version == version.version,
            )
        )
        self._add_property_rows(version)
        try:
            self._session.flush()
        except IntegrityError as error:
            raise ObjectTemplatePersistenceError(
                "ObjectTemplate version replacement failed."
            ) from error

"""Representative raw PostgreSQL enforcement for frozen structural families."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import Executable

from netauto.persistence.metadata import (
    datatype_versions,
    datatypes,
    object_components,
    object_lifecycle_events,
    object_template_components,
    object_template_properties,
    object_template_versions,
    object_templates,
    objects,
    relationship_definitions,
    relationship_resolutions,
    relationships,
    runtime_relationship_resolutions,
)


def _fails_integrity(connection: Connection, statement: Executable) -> None:
    # Kept local and raw: this is persistence evidence, not domain error mapping.
    with pytest.raises(IntegrityError):
        with connection.begin_nested():
            connection.execute(statement)


@pytest.mark.postgresql
def test_model_constraints_cascade_and_restrict(
    migrated_database_engine: Engine,
) -> None:
    datatype_id = uuid4()
    template_id = uuid4()
    target_template_id = uuid4()
    with migrated_database_engine.begin() as connection:
        connection.execute(
            datatypes.insert().values(
                id=datatype_id, namespace="s01", name="string_value"
            )
        )
        connection.execute(
            datatype_versions.insert().values(
                datatype_id=datatype_id,
                version=1,
                revision=1,
                status="DRAFT",
                base_type="core.string",
                constraints={},
            )
        )

        _fails_integrity(
            connection,
            datatypes.insert().values(id=uuid4(), namespace="s01", name="string_value"),
        )
        _fails_integrity(
            connection,
            datatype_versions.insert().values(
                datatype_id=datatype_id,
                version=0,
                revision=1,
                status="DRAFT",
                base_type="core.string",
                constraints={},
            ),
        )
        _fails_integrity(
            connection,
            datatype_versions.insert().values(
                datatype_id=datatype_id,
                version=2,
                revision=1,
                status="DRAFT",
                base_type="core.string",
                constraints=[],
            ),
        )

        connection.execute(
            object_templates.insert(),
            [
                {
                    "id": template_id,
                    "namespace": "s01",
                    "name": "source",
                    "abstract": False,
                },
                {
                    "id": target_template_id,
                    "namespace": "s01",
                    "name": "target",
                    "abstract": False,
                },
            ],
        )
        connection.execute(
            object_template_versions.insert().values(
                template_id=template_id,
                version=1,
                revision=1,
                status="DRAFT",
            )
        )
        connection.execute(
            object_template_properties.insert().values(
                template_id=template_id,
                template_version=1,
                name="value",
                position=1,
                datatype_id=datatype_id,
                datatype_version=1,
                value_mode="SCALAR",
                required=False,
            )
        )
        _fails_integrity(
            connection,
            object_template_properties.insert().values(
                template_id=template_id,
                template_version=1,
                name="broken_pin",
                position=2,
                datatype_id=datatype_id,
                datatype_version=99,
                value_mode="SCALAR",
                required=False,
            ),
        )
        _fails_integrity(
            connection,
            object_template_components.insert().values(
                template_id=template_id,
                template_version=1,
                name="missing_target",
                position=1,
                target_template_id=uuid4(),
            ),
        )
        connection.execute(
            object_template_components.insert().values(
                template_id=template_id,
                template_version=1,
                name="children",
                position=1,
                target_template_id=target_template_id,
            )
        )
        _fails_integrity(
            connection,
            object_templates.delete().where(
                object_templates.c.id == target_template_id
            ),
        )

        cascade_datatype_id = uuid4()
        connection.execute(
            datatypes.insert().values(
                id=cascade_datatype_id, namespace="s01", name="cascade_value"
            )
        )
        connection.execute(
            datatype_versions.insert().values(
                datatype_id=cascade_datatype_id,
                version=1,
                revision=1,
                status="DRAFT",
                base_type="core.string",
                constraints={},
            )
        )
        connection.execute(
            datatypes.delete().where(datatypes.c.id == cascade_datatype_id)
        )
        assert (
            connection.scalar(
                select(func.count())
                .select_from(datatype_versions)
                .where(datatype_versions.c.datatype_id == cascade_datatype_id)
            )
            == 0
        )


@pytest.mark.postgresql
def test_runtime_authorities_and_historical_lifecycle_defaults(
    migrated_database_engine: Engine,
) -> None:
    template_id = uuid4()
    parent_a, parent_b, child = uuid4(), uuid4(), uuid4()
    definition_a, definition_b = uuid4(), uuid4()
    resolution_a, resolution_b = uuid4(), uuid4()
    relationship_id = uuid4()
    historical_object_id = uuid4()

    with migrated_database_engine.begin() as connection:
        connection.execute(
            object_templates.insert().values(
                id=template_id,
                namespace="s01",
                name="runtime",
                abstract=False,
            )
        )
        connection.execute(
            object_template_versions.insert().values(
                template_id=template_id,
                version=1,
                revision=1,
                status="DRAFT",
            )
        )
        connection.execute(
            objects.insert(),
            [
                {
                    "id": object_id,
                    "canonical_name": str(object_id),
                    "template_id": template_id,
                    "template_version": 1,
                    "properties": {},
                }
                for object_id in (parent_a, parent_b, child)
            ],
        )
        _fails_integrity(
            connection,
            objects.insert().values(
                id=uuid4(),
                canonical_name="bad pin",
                template_id=template_id,
                template_version=99,
                properties={},
            ),
        )

        connection.execute(
            object_components.insert().values(
                child_object_id=child,
                parent_object_id=parent_a,
                slot_name="children",
            )
        )
        _fails_integrity(
            connection,
            object_components.insert().values(
                child_object_id=child,
                parent_object_id=parent_b,
                slot_name="children",
            ),
        )

        connection.execute(
            relationship_definitions.insert(),
            [
                {"id": definition_a, "symmetric": True},
                {"id": definition_b, "symmetric": True},
            ],
        )
        connection.execute(
            relationship_resolutions.insert(),
            [
                {
                    "id": resolution_a,
                    "relationship_definition_id": definition_a,
                    "from_template_id": template_id,
                    "to_template_id": template_id,
                    "name": "related_a",
                },
                {
                    "id": resolution_b,
                    "relationship_definition_id": definition_b,
                    "from_template_id": template_id,
                    "to_template_id": template_id,
                    "name": "related_b",
                },
            ],
        )
        connection.execute(
            relationships.insert().values(
                id=relationship_id, relationship_definition_id=definition_a
            )
        )
        _fails_integrity(
            connection,
            runtime_relationship_resolutions.insert().values(
                relationship_id=relationship_id,
                relationship_definition_id=definition_a,
                resolution_id=resolution_b,
                from_object_id=parent_a,
                to_object_id=parent_b,
            ),
        )
        connection.execute(
            runtime_relationship_resolutions.insert().values(
                relationship_id=relationship_id,
                relationship_definition_id=definition_a,
                resolution_id=resolution_a,
                from_object_id=parent_a,
                to_object_id=parent_b,
            )
        )
        connection.execute(
            relationships.delete().where(relationships.c.id == relationship_id)
        )
        assert (
            connection.scalar(
                select(func.count()).select_from(runtime_relationship_resolutions)
            )
            == 0
        )

        first = connection.execute(
            object_lifecycle_events.insert()
            .values(
                kind="CREATED",
                object_id=historical_object_id,
                canonical_name="already deleted",
                after_state={},
            )
            .returning(
                object_lifecycle_events.c.id,
                object_lifecycle_events.c.occurred_at,
            )
        ).one()
        second = connection.execute(
            object_lifecycle_events.insert()
            .values(
                kind="DELETED",
                object_id=historical_object_id,
                canonical_name="already deleted",
                before_state={},
            )
            .returning(
                object_lifecycle_events.c.id,
                object_lifecycle_events.c.occurred_at,
            )
        ).one()

        assert isinstance(first.id, UUID)
        assert isinstance(second.id, UUID)
        assert first.id != second.id
        assert first.occurred_at == second.occurred_at

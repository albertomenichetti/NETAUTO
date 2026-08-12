from __future__ import annotations

from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from netauto.api.app import create_app
from netauto.application.unit_of_work import ObjectUnitOfWork
from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataType,
    DataTypeFactory,
    DataTypeVersion,
    DataTypeVersioningService,
    DataTypeVersionStatus,
)
from netauto.core.object import Object, ObjectPersistenceError
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateComponent,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.persistence.memory.datatype_repository import InMemoryDataTypeRepository
from netauto.persistence.memory.object_change_repository import (
    InMemoryObjectChangeRepository,
)
from netauto.persistence.memory.object_repository import InMemoryObjectRepository
from netauto.persistence.memory.objecttemplate_repository import InMemoryObjectTemplateRepository
from netauto.persistence.memory.relationship_repository import (
    InMemoryRelationshipDefinitionRepository,
    InMemoryRelationshipRepository,
)


class FakeUnitOfWork(ObjectUnitOfWork):
    def __init__(
        self,
        datatypes: InMemoryDataTypeRepository,
        object_templates: InMemoryObjectTemplateRepository,
        objects: InMemoryObjectRepository,
        object_changes: InMemoryObjectChangeRepository,
        relationships: InMemoryRelationshipRepository,
        relationship_definitions: InMemoryRelationshipDefinitionRepository,
        commit_counter: list[int],
    ) -> None:
        self._datatypes = datatypes
        self._object_templates = object_templates
        self._objects = objects
        self._object_changes = object_changes
        self._relationships = relationships
        self._relationship_definitions = relationship_definitions
        self._commit_counter = commit_counter

    @property
    def datatypes(self) -> InMemoryDataTypeRepository:
        return self._datatypes

    @property
    def object_templates(self) -> InMemoryObjectTemplateRepository:
        return self._object_templates

    @property
    def relationship_definitions(self) -> InMemoryRelationshipDefinitionRepository:
        return self._relationship_definitions

    @property
    def relationships(self) -> InMemoryRelationshipRepository:
        return self._relationships

    @property
    def objects(self) -> InMemoryObjectRepository:
        return self._objects

    @property
    def object_changes(self) -> InMemoryObjectChangeRepository:
        return self._object_changes

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self._commit_counter[0] += 1


class BrokenObjectRepository(InMemoryObjectRepository):
    def list_by_template_version(
        self,
        template_id: UUID,
        template_version: int,
    ) -> tuple[Object, ...]:
        raise ObjectPersistenceError("boom")


class BrokenObjectUnitOfWork(FakeUnitOfWork):
    def __init__(self) -> None:
        datatypes = InMemoryDataTypeRepository()
        object_templates = InMemoryObjectTemplateRepository()
        objects = BrokenObjectRepository()
        template_id = UUID("00000000-0000-0000-0000-000000000001")
        template = ObjectTemplate(
            id=template_id,
            namespace="network",
            name="device",
            description="device template",
            abstract=False,
        )
        object_templates.add(template)
        object_templates.add_version(
            ObjectTemplateVersion(
                template_id=template_id,
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT,
            )
        )
        object_templates.replace_version(
            ObjectTemplateVersion(
                template_id=template_id,
                version=1,
                status=ObjectTemplateVersionStatus.PUBLISHED,
            )
        )
        object_templates.add_version(
            ObjectTemplateVersion(
                template_id=template_id,
                version=2,
                status=ObjectTemplateVersionStatus.DRAFT,
            )
        )
        object_templates.replace_version(
            ObjectTemplateVersion(
                template_id=template_id,
                version=2,
                status=ObjectTemplateVersionStatus.PUBLISHED,
            )
        )
        super().__init__(
            datatypes,
            object_templates,
            objects,
            InMemoryObjectChangeRepository(),
            InMemoryRelationshipRepository(),
            InMemoryRelationshipDefinitionRepository(),
            [0],
        )


@pytest.fixture
def client_context() -> (
    Generator[
        tuple[
            TestClient,
            InMemoryDataTypeRepository,
            InMemoryObjectTemplateRepository,
            InMemoryObjectRepository,
            list[int],
        ],
        None,
        None,
    ]
):
    datatypes = InMemoryDataTypeRepository()
    object_templates = InMemoryObjectTemplateRepository()
    objects = InMemoryObjectRepository()
    object_changes = InMemoryObjectChangeRepository()
    relationships = InMemoryRelationshipRepository()
    relationship_definitions = InMemoryRelationshipDefinitionRepository()
    commits = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(
            datatypes,
            object_templates,
            objects,
            object_changes,
            relationships,
            relationship_definitions,
            commits,
        )

    with TestClient(
        create_app(
            factory,
            model_write_uow_factory=factory,
            ownership_graph_uow_factory=factory,
        )
    ) as client:
        yield client, datatypes, object_templates, objects, commits


def _datatype(
    *,
    namespace: str = "network",
    name: str = "hostname",
    base_type: str = "core.string",
    constraints: tuple[Constraint, ...] = (),
) -> tuple[DataType, DataTypeVersion]:
    datatype, draft = DataTypeFactory().create(
        namespace=namespace,
        name=name,
        description=f"{name} datatype",
        base_type=base_type,
        constraints=constraints,
    )
    return datatype, DataTypeVersioningService().publish(draft)


def _store_datatype_versions(
    repo: InMemoryDataTypeRepository,
    datatype: DataType,
    versions: tuple[DataTypeVersion, ...],
) -> None:
    repo.add(datatype)
    for version in versions:
        draft = DataTypeVersion(
            datatype_id=version.datatype_id,
            version=version.version,
            status=DataTypeVersionStatus.DRAFT,
            base_type=version.base_type,
            constraints=version.constraints,
        )
        repo.add_version(draft)
        if version.status is DataTypeVersionStatus.PUBLISHED:
            repo.replace_version(version)
        elif version.status is DataTypeVersionStatus.DEPRECATED:
            repo.replace_version(DataTypeVersioningService().publish(draft))
            repo.replace_version(version)


def _property(
    name: str,
    *,
    datatype_id: UUID,
    datatype_version: int,
    required: bool = False,
) -> ObjectTemplateProperty:
    return ObjectTemplateProperty(
        name=name,
        datatype_id=datatype_id,
        datatype_version=datatype_version,
        required=required,
    )


def _component(name: str, *, template_id: UUID) -> ObjectTemplateComponent:
    return ObjectTemplateComponent(name=name, template_id=template_id)


def _store_template_versions(
    repo: InMemoryObjectTemplateRepository,
    *,
    name: str,
    versions: tuple[ObjectTemplateVersion, ...],
    abstract: bool = False,
) -> ObjectTemplate:
    template = ObjectTemplate(
        id=versions[0].template_id,
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=abstract,
    )
    repo.add(template)
    for version in versions:
        draft = ObjectTemplateVersion(
            template_id=version.template_id,
            version=version.version,
            status=ObjectTemplateVersionStatus.DRAFT,
            parent=version.parent,
            properties=version.properties,
            components=version.components,
        )
        repo.add_version(draft)
        if version.status is ObjectTemplateVersionStatus.PUBLISHED:
            repo.replace_version(version)
        elif version.status is ObjectTemplateVersionStatus.DEPRECATED:
            repo.replace_version(
                ObjectTemplateVersion(
                    template_id=draft.template_id,
                    version=draft.version,
                    status=ObjectTemplateVersionStatus.PUBLISHED,
                    parent=draft.parent,
                    properties=draft.properties,
                    components=draft.components,
                )
            )
            repo.replace_version(version)
    return template


def _version(
    template_id: UUID,
    *,
    version: int,
    status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.PUBLISHED,
    parent: ObjectTemplateVersionRef | None = None,
    properties: tuple[ObjectTemplateProperty, ...] = (),
    components: tuple[ObjectTemplateComponent, ...] = (),
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=status,
        parent=parent,
        properties=properties,
        components=components,
    )


def _store_object(
    repo: InMemoryObjectRepository,
    *,
    template_id: UUID,
    template_version: int,
    properties: dict[str, object],
) -> Object:
    object_value = Object(
        id=uuid4(),
        template_id=template_id,
        template_version=template_version,
        properties=properties,
    )
    repo.add(object_value)
    return object_value


def test_migration_analysis_request_validation_is_strict(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _templates, _objects, _commits = client_context

    cases = [
        ({}, "/query/target_version"),
        ({"target_version": 0}, "/query/target_version"),
        ({"target_version": "nope"}, "/query/target_version"),
    ]

    for params, path in cases:
        response = client.get(
            f"/api/v1/object-templates/{uuid4()}/versions/1/migration-analysis",
            params=params,
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "request_validation_failed"
        assert any(detail["path"] == path for detail in response.json()["error"]["details"])


def test_migrate_request_validation_is_strict(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _templates, _objects, _commits = client_context
    payloads = [
        ({"target_version": True, "property_values": {}}, "/body/target_version"),
        ({"target_version": "2", "property_values": {}}, "/body/target_version"),
        ({"target_version": 0, "property_values": {}}, "/body/target_version"),
        ({"target_version": 2, "property_values": []}, "/body/property_values"),
        ({"target_version": 2, "property_values": {}, "extra": 1}, "/body/extra"),
    ]

    for payload, path in payloads:
        response = client.post(
            f"/api/v1/object-templates/{uuid4()}/versions/1/migrate-objects",
            json=payload,
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "request_validation_failed"
        assert any(detail["path"] == path for detail in response.json()["error"]["details"])


def test_analysis_response_reports_additive_delta(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, datatypes, templates, _objects, commits = client_context
    hostname, hostname_v1 = _datatype(name="hostname")
    serial, serial_v1 = _datatype(name="serialnumber")
    power_supply = ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name="power_supply",
        description="power_supply template",
        abstract=False,
    )
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, serial, (serial_v1,))
    _store_template_versions(
        templates,
        name="power_supply",
        versions=(_version(power_supply.id, version=1),),
    )

    template_id = uuid4()
    _store_template_versions(
        templates,
        name="device",
        versions=(
            _version(
                template_id,
                version=1,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname.id,
                        datatype_version=1,
                        required=True,
                    ),
                ),
            ),
            _version(
                template_id,
                version=2,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname.id,
                        datatype_version=1,
                        required=True,
                    ),
                    _property(
                        "serialnumber",
                        datatype_id=serial.id,
                        datatype_version=1,
                        required=True,
                    ),
                ),
                components=(_component("power_supplies", template_id=power_supply.id),),
            ),
        ),
    )

    response = client.get(
        f"/api/v1/object-templates/{template_id}/versions/1/migration-analysis",
        params={"target_version": 2},
    )

    assert response.status_code == 200
    assert response.json() == {
        "template_id": str(template_id),
        "source_version": 1,
        "target_version": 2,
        "automatic": True,
        "added_properties": [{"name": "serialnumber", "required": True}],
        "added_components": [{"name": "power_supplies", "template_id": str(power_supply.id)}],
        "blocking_changes": [],
    }
    assert commits[0] == 0


def test_migrate_objects_success_and_atomic_commit(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, datatypes, templates, objects, commits = client_context
    hostname, hostname_v1 = _datatype(name="hostname")
    serial, serial_v1 = _datatype(name="serialnumber")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, serial, (serial_v1,))

    template_id = uuid4()
    _store_template_versions(
        templates,
        name="device",
        versions=(
            _version(
                template_id,
                version=1,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname.id,
                        datatype_version=1,
                        required=True,
                    ),
                ),
            ),
            _version(
                template_id,
                version=2,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname.id,
                        datatype_version=1,
                        required=True,
                    ),
                    _property(
                        "serialnumber",
                        datatype_id=serial.id,
                        datatype_version=1,
                        required=True,
                    ),
                ),
            ),
        ),
    )
    first = _store_object(
        objects,
        template_id=template_id,
        template_version=1,
        properties={"hostname": "a"},
    )
    second = _store_object(
        objects,
        template_id=template_id,
        template_version=1,
        properties={"hostname": "b"},
    )
    other = _store_object(
        objects,
        template_id=template_id,
        template_version=2,
        properties={"hostname": "c"},
    )

    response = client.post(
        f"/api/v1/object-templates/{template_id}/versions/1/migrate-objects",
        json={"target_version": 2, "property_values": {"serialnumber": "UNKNOWN"}},
    )

    assert response.status_code == 200
    assert response.json() == {
        "template_id": str(template_id),
        "source_version": 1,
        "target_version": 2,
        "migrated_count": 2,
    }
    assert objects.get(first.id) == Object(
        id=first.id,
        template_id=template_id,
        template_version=2,
        properties={"hostname": "a", "serialnumber": "UNKNOWN"},
    )
    assert objects.get(second.id) == Object(
        id=second.id,
        template_id=template_id,
        template_version=2,
        properties={"hostname": "b", "serialnumber": "UNKNOWN"},
    )
    assert objects.get(other.id) == other
    assert commits[0] == 1


def test_migrate_structural_and_validation_failures_map_correctly(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, datatypes, templates, objects, commits = client_context
    hostname, hostname_v1 = _datatype(name="hostname")
    vlan, vlan_v1 = _datatype(
        name="vlan",
        base_type="core.integer",
        constraints=(Constraint(name=ConstraintName.MINIMUM, value=1),),
    )
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))
    _store_datatype_versions(datatypes, vlan, (vlan_v1,))

    template_id = uuid4()
    _store_template_versions(
        templates,
        name="device",
        versions=(
            _version(
                template_id,
                version=1,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname.id,
                        datatype_version=1,
                        required=True,
                    ),
                ),
            ),
            _version(
                template_id,
                version=2,
                properties=(
                    _property("hostname", datatype_id=vlan.id, datatype_version=1, required=True),
                ),
            ),
            _version(
                template_id,
                version=3,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname.id,
                        datatype_version=1,
                        required=True,
                    ),
                    _property("vlan", datatype_id=vlan.id, datatype_version=1, required=True),
                ),
            ),
            _version(
                template_id,
                version=4,
                status=ObjectTemplateVersionStatus.DRAFT,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname.id,
                        datatype_version=1,
                        required=True,
                    ),
                ),
            ),
        ),
    )
    source = _store_object(
        objects,
        template_id=template_id,
        template_version=1,
        properties={"hostname": "r1"},
    )

    blocked = client.post(
        f"/api/v1/object-templates/{template_id}/versions/1/migrate-objects",
        json={"target_version": 2, "property_values": {}},
    )
    missing_value = client.post(
        f"/api/v1/object-templates/{template_id}/versions/1/migrate-objects",
        json={"target_version": 3, "property_values": {}},
    )
    unexpected_value = client.post(
        f"/api/v1/object-templates/{template_id}/versions/1/migrate-objects",
        json={"target_version": 3, "property_values": {"hostname": "new"}},
    )
    invalid_value = client.post(
        f"/api/v1/object-templates/{template_id}/versions/1/migrate-objects",
        json={"target_version": 3, "property_values": {"vlan": "not-an-int"}},
    )
    target_draft = client.post(
        f"/api/v1/object-templates/{template_id}/versions/1/migrate-objects",
        json={"target_version": 4, "property_values": {}},
    )

    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "object_migration_blocked"
    assert missing_value.status_code == 422
    assert missing_value.json()["error"]["code"] == "missing_object_migration_property_value"
    assert unexpected_value.status_code == 422
    assert (
        unexpected_value.json()["error"]["code"]
        == "unexpected_object_migration_property_value"
    )
    assert invalid_value.status_code == 422
    assert invalid_value.json()["error"]["code"] == "object_validation_failed"
    assert invalid_value.json()["error"]["details"][0]["path"] == "/properties/vlan"
    assert target_draft.status_code == 409
    assert target_draft.json()["error"]["code"] == "object_migration_target_version_not_published"
    assert objects.get(source.id) == source
    assert commits[0] == 0


@pytest.mark.parametrize("target_version", [2, 1])
def test_migration_direction_error_maps_to_409(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
    target_version: int,
) -> None:
    client, datatypes, templates, objects, commits = client_context
    hostname, hostname_v1 = _datatype(name="hostname")
    _store_datatype_versions(datatypes, hostname, (hostname_v1,))

    template_id = uuid4()
    _store_template_versions(
        templates,
        name="device",
        versions=(
            _version(
                template_id,
                version=1,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname.id,
                        datatype_version=1,
                        required=True,
                    ),
                ),
            ),
            _version(
                template_id,
                version=2,
                properties=(
                    _property(
                        "hostname",
                        datatype_id=hostname.id,
                        datatype_version=1,
                        required=True,
                    ),
                ),
            ),
        ),
    )
    source = _store_object(
        objects,
        template_id=template_id,
        template_version=1,
        properties={"hostname": "r1"},
    )

    analysis = client.get(
        f"/api/v1/object-templates/{template_id}/versions/2/migration-analysis",
        params={"target_version": target_version},
    )
    execute = client.post(
        f"/api/v1/object-templates/{template_id}/versions/2/migrate-objects",
        json={"target_version": target_version, "property_values": {}},
    )

    assert analysis.status_code == 409
    assert (
        analysis.json()["error"]["code"]
        == "object_migration_target_version_not_newer"
    )
    assert execute.status_code == 409
    assert (
        execute.json()["error"]["code"]
        == "object_migration_target_version_not_newer"
    )
    assert objects.get(source.id) == source
    assert commits[0] == 0


def test_object_migration_persistence_error_maps_to_500() -> None:
    def factory() -> BrokenObjectUnitOfWork:
        return BrokenObjectUnitOfWork()

    with TestClient(
        create_app(
            factory,
            model_write_uow_factory=factory,
            ownership_graph_uow_factory=factory,
        )
    ) as client:
        response = client.post(
            "/api/v1/object-templates/00000000-0000-0000-0000-000000000001/versions/1/migrate-objects",
            json={"target_version": 2, "property_values": {}},
        )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "persistence_error"


def test_openapi_contains_object_migration_routes_and_schemas(
    client_context: tuple[
        TestClient,
        InMemoryDataTypeRepository,
        InMemoryObjectTemplateRepository,
        InMemoryObjectRepository,
        list[int],
    ],
) -> None:
    client, _datatypes, _templates, _objects, _commits = client_context

    response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    assert (
        "/api/v1/object-templates/{template_id}/versions/{version}/migration-analysis"
        in payload["paths"]
    )
    assert (
        "/api/v1/object-templates/{template_id}/versions/{version}/migrate-objects"
        in payload["paths"]
    )
    assert "ObjectTemplateMigrationAnalysisResponse" in payload["components"]["schemas"]
    assert "MigrateObjectsRequest" in payload["components"]["schemas"]
    assert "MigrateObjectsResponse" in payload["components"]["schemas"]

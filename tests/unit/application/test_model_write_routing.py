from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import FastAPI

from netauto.api.app import create_app
from netauto.application.datatype import DataTypeApplicationService
from netauto.application.object import ObjectApplicationService
from netauto.application.objecttemplate import (
    ObjectTemplateApplicationService,
    ObjectTemplatePropertySpec,
)
from netauto.application.relationship import (
    RelationshipApplicationService,
    RelationshipDefinitionApplicationService,
)
from netauto.application.unit_of_work import (
    DataTypeUnitOfWork,
    ObjectTemplateUnitOfWork,
    RelationshipDefinitionUnitOfWork,
)
from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataType,
    DataTypeVersion,
    DataTypeVersionStatus,
    PrimitiveTypeRegistry,
)
from netauto.core.object import Object
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateComponent,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import RelationshipDefinition
from netauto.persistence.memory.datatype_repository import InMemoryDataTypeRepository
from netauto.persistence.memory.object_change_repository import (
    InMemoryObjectChangeRepository,
)
from netauto.persistence.memory.object_repository import InMemoryObjectRepository
from netauto.persistence.memory.objecttemplate_repository import (
    InMemoryObjectTemplateRepository,
)
from netauto.persistence.memory.relationship_repository import (
    InMemoryRelationshipDefinitionRepository,
    InMemoryRelationshipRepository,
)


class FullFakeUnitOfWork(
    DataTypeUnitOfWork,
    ObjectTemplateUnitOfWork,
    RelationshipDefinitionUnitOfWork,
):
    def __init__(
        self,
        *,
        datatypes: InMemoryDataTypeRepository,
        object_templates: InMemoryObjectTemplateRepository,
        objects: InMemoryObjectRepository,
        object_changes: InMemoryObjectChangeRepository,
        relationships: InMemoryRelationshipRepository,
        relationship_definitions: InMemoryRelationshipDefinitionRepository,
    ) -> None:
        self._datatypes = datatypes
        self._object_templates = object_templates
        self._objects = objects
        self._object_changes = object_changes
        self._relationships = relationships
        self._relationship_definitions = relationship_definitions

    @property
    def datatypes(self) -> InMemoryDataTypeRepository:
        return self._datatypes

    @property
    def object_templates(self) -> InMemoryObjectTemplateRepository:
        return self._object_templates

    @property
    def objects(self) -> InMemoryObjectRepository:
        return self._objects

    @property
    def object_changes(self) -> InMemoryObjectChangeRepository:
        return self._object_changes

    @property
    def relationships(self) -> InMemoryRelationshipRepository:
        return self._relationships

    @property
    def relationship_definitions(self) -> InMemoryRelationshipDefinitionRepository:
        return self._relationship_definitions

    def __enter__(self) -> FullFakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        return None


class CountingFactory:
    def __init__(self, uow: FullFakeUnitOfWork) -> None:
        self._uow = uow
        self.calls = 0

    def __call__(self) -> FullFakeUnitOfWork:
        self.calls += 1
        return self._uow


def _datatype(
    *,
    datatype_id: UUID | None = None,
    namespace: str = "network",
    name: str = "hostname",
    description: str = "hostname datatype",
) -> DataType:
    return DataType(
        id=datatype_id or uuid4(),
        namespace=namespace,
        name=name,
        description=description,
    )


def _datatype_version(
    datatype_id: UUID,
    *,
    version: int,
    status,
    constraints: tuple[Constraint, ...] = (),
) -> DataTypeVersion:
    return DataTypeVersion(
        datatype_id=datatype_id,
        version=version,
        status=status,
        base_type=PrimitiveTypeRegistry().get("core.string"),
        constraints=constraints,
    )


def _template(
    *,
    template_id: UUID | None = None,
    namespace: str = "network",
    name: str = "device",
) -> ObjectTemplate:
    return ObjectTemplate(
        id=template_id or uuid4(),
        namespace=namespace,
        name=name,
        description=f"{name} template",
        abstract=False,
    )


def _template_version(
    template_id: UUID,
    *,
    version: int,
    status: ObjectTemplateVersionStatus,
    parent: ObjectTemplateVersionRef | None = None,
    properties: tuple[ObjectTemplateProperty, ...] = (),
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=status,
        parent=parent,
        properties=properties,
    )


def _property(
    *,
    name: str,
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


def _full_uow() -> FullFakeUnitOfWork:
    return FullFakeUnitOfWork(
        datatypes=InMemoryDataTypeRepository(),
        object_templates=InMemoryObjectTemplateRepository(),
        objects=InMemoryObjectRepository(),
        object_changes=InMemoryObjectChangeRepository(),
        relationships=InMemoryRelationshipRepository(),
        relationship_definitions=InMemoryRelationshipDefinitionRepository(),
    )


def test_datatype_service_routes_mutations_to_model_write_and_reads_to_ordinary() -> None:
    def make_service() -> tuple[
        DataTypeApplicationService,
        FullFakeUnitOfWork,
        CountingFactory,
        CountingFactory,
    ]:
        uow = _full_uow()
        ordinary = CountingFactory(uow)
        model = CountingFactory(uow)
        service = DataTypeApplicationService(
            ordinary,
            model_write_uow_factory=model,
        )
        return service, uow, ordinary, model

    service, uow, ordinary, model = make_service()
    created_datatype, created_version = service.create_datatype(
        namespace="network",
        name="hostname",
        description="hostname datatype",
        base_type="core.string",
        constraints=(),
    )
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    datatype = _datatype()
    draft = _datatype_version(
        datatype.id,
        version=1,
        status=DataTypeVersionStatus.DRAFT,
    )
    uow.datatypes.add(datatype)
    uow.datatypes.add_version(draft)
    service.revise_version(
        datatype_id=datatype.id,
        version=1,
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    datatype = _datatype()
    source = _datatype_version(
        datatype.id,
        version=1,
        status=DataTypeVersionStatus.PUBLISHED,
    )
    uow.datatypes.add(datatype)
    uow.datatypes.add_version(
        _datatype_version(
            datatype.id,
            version=1,
            status=DataTypeVersionStatus.DRAFT,
        )
    )
    uow.datatypes.replace_version(source)
    service.create_next_version(datatype_id=datatype.id, source_version=1)
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    datatype = _datatype()
    draft = _datatype_version(
        datatype.id,
        version=1,
        status=DataTypeVersionStatus.DRAFT,
    )
    uow.datatypes.add(datatype)
    uow.datatypes.add_version(draft)
    service.publish_version(datatype_id=datatype.id, version=1)
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    datatype = _datatype()
    published = _datatype_version(
        datatype.id,
        version=1,
        status=DataTypeVersionStatus.PUBLISHED,
    )
    uow.datatypes.add(datatype)
    uow.datatypes.add_version(
        _datatype_version(
            datatype.id,
            version=1,
            status=DataTypeVersionStatus.DRAFT,
        )
    )
    uow.datatypes.replace_version(published)
    service.deprecate_version(datatype_id=datatype.id, version=1)
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    datatype = _datatype()
    draft = _datatype_version(
        datatype.id,
        version=1,
        status=DataTypeVersionStatus.DRAFT,
    )
    uow.datatypes.add(datatype)
    uow.datatypes.add_version(draft)
    service.delete_datatype(datatype.id)
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    datatype = _datatype()
    version = _datatype_version(
        datatype.id,
        version=1,
        status=DataTypeVersionStatus.DRAFT,
    )
    uow.datatypes.add(datatype)
    uow.datatypes.add_version(version)
    assert service.list_datatypes() == (datatype,)
    assert service.get_datatype(datatype.id) == datatype
    assert service.get_datatype_by_name(datatype.namespace, datatype.name) == datatype
    assert service.list_versions(datatype.id) == (version,)
    assert service.get_version(datatype.id, 1) == version
    assert ordinary.calls == 5
    assert model.calls == 0


def test_object_template_service_routes_mutations_to_model_write_and_reads_to_ordinary(
) -> None:
    def make_service() -> tuple[
        ObjectTemplateApplicationService,
        FullFakeUnitOfWork,
        CountingFactory,
        CountingFactory,
    ]:
        uow = _full_uow()
        ordinary = CountingFactory(uow)
        model = CountingFactory(uow)
        service = ObjectTemplateApplicationService(
            ordinary,
            model_write_uow_factory=model,
        )
        return service, uow, ordinary, model

    datatype = _datatype()
    published_datatype = _datatype_version(
        datatype.id,
        version=1,
        status=DataTypeVersionStatus.PUBLISHED,
    )

    service, uow, ordinary, model = make_service()
    uow.datatypes.add(datatype)
    uow.datatypes.add_version(
        _datatype_version(
            datatype.id,
            version=1,
            status=DataTypeVersionStatus.DRAFT,
        )
    )
    uow.datatypes.replace_version(published_datatype)
    template, _version = service.create_object_template(
        namespace="network",
        name="device",
        description="device template",
        abstract=False,
        parent=None,
        properties=(
            ObjectTemplatePropertySpec(
                name="hostname",
                datatype_id=datatype.id,
            ),
        ),
    )
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    uow.datatypes.add(datatype)
    uow.datatypes.add_version(
        _datatype_version(
            datatype.id,
            version=1,
            status=DataTypeVersionStatus.DRAFT,
        )
    )
    uow.datatypes.replace_version(published_datatype)
    uow.object_templates.add(template)
    draft = _template_version(
        template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(
            _property(name="hostname", datatype_id=datatype.id, datatype_version=1),
        ),
    )
    uow.object_templates.add_version(draft)
    service.revise_version(
        template_id=template.id,
        version=1,
        parent=None,
        properties=(
            ObjectTemplatePropertySpec(name="hostname", datatype_id=datatype.id),
        ),
    )
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    uow.object_templates.add(template)
    published = _template_version(
        template.id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
    )
    uow.object_templates.add_version(
        _template_version(
            template.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
        )
    )
    uow.object_templates.replace_version(published)
    service.create_next_version(template_id=template.id, source_version=1)
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    uow.object_templates.add(template)
    draft = _template_version(
        template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
    )
    uow.object_templates.add_version(draft)
    service.publish_version(template_id=template.id, version=1)
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    uow.object_templates.add(template)
    published = _template_version(
        template.id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
    )
    uow.object_templates.add_version(
        _template_version(
            template.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
        )
    )
    uow.object_templates.replace_version(published)
    service.deprecate_version(template_id=template.id, version=1)
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    uow.object_templates.add(template)
    uow.object_templates.add_version(
        _template_version(
            template.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
        )
    )
    service.delete_object_template(template.id)
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    uow.object_templates.add(template)
    version = _template_version(
        template.id,
        version=1,
        status=ObjectTemplateVersionStatus.DRAFT,
    )
    uow.object_templates.add_version(version)
    assert service.list_object_templates() == (template,)
    assert service.get_object_template(template.id) == template
    assert service.get_object_template_by_name(template.namespace, template.name) == template
    assert service.list_versions(template.id) == (version,)
    assert service.get_version(template.id, 1) == version
    assert ordinary.calls == 5
    assert model.calls == 0


def test_relationship_definition_service_routes_mutations_to_model_write_and_reads_to_ordinary(
) -> None:
    def make_service() -> tuple[
        RelationshipDefinitionApplicationService,
        FullFakeUnitOfWork,
        CountingFactory,
        CountingFactory,
    ]:
        uow = _full_uow()
        ordinary = CountingFactory(uow)
        model = CountingFactory(uow)
        service = RelationshipDefinitionApplicationService(
            ordinary,
            model_write_uow_factory=model,
        )
        return service, uow, ordinary, model

    source = _template(name="source")
    target = _template(name="target")
    source_v1 = _template_version(
        source.id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
    )
    target_v1 = _template_version(
        target.id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
    )

    service, uow, ordinary, model = make_service()
    uow.object_templates.add(source)
    uow.object_templates.add(target)
    uow.object_templates.add_version(
        _template_version(source.id, version=1, status=ObjectTemplateVersionStatus.DRAFT)
    )
    uow.object_templates.replace_version(source_v1)
    uow.object_templates.add_version(
        _template_version(target.id, version=1, status=ObjectTemplateVersionStatus.DRAFT)
    )
    uow.object_templates.replace_version(target_v1)
    created = service.create_relationship_definition(
        source_template_id=source.id,
        target_template_id=target.id,
        forward_name="uses",
        reverse_name="is_used_by",
    )
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    uow.relationship_definitions.add(created)
    service.delete_relationship_definition(created.id)
    assert ordinary.calls == 0
    assert model.calls == 1

    service, uow, ordinary, model = make_service()
    uow.relationship_definitions.add(created)
    assert service.list_relationship_definitions() == (created,)
    assert service.get_relationship_definition(created.id) == created
    assert ordinary.calls == 2
    assert model.calls == 0


def test_create_app_wires_model_plane_and_runtime_services_to_expected_factories(
) -> None:
    ordinary_uow = _full_uow()
    model_uow = _full_uow()
    ownership_uow = _full_uow()

    def ordinary() -> FullFakeUnitOfWork:
        return ordinary_uow

    def model() -> FullFakeUnitOfWork:
        return model_uow

    def ownership() -> FullFakeUnitOfWork:
        return ownership_uow

    app: FastAPI = create_app(
        ordinary,
        model_write_uow_factory=model,
        ownership_graph_uow_factory=ownership,
    )

    assert app.state.datatype_service._uow_factory is ordinary
    assert app.state.datatype_service._model_write_uow_factory is model
    assert app.state.object_template_service._uow_factory is ordinary
    assert app.state.object_template_service._model_write_uow_factory is model
    assert app.state.relationship_definition_service._uow_factory is ordinary
    assert app.state.relationship_definition_service._model_write_uow_factory is model
    assert app.state.object_service._uow_factory is ordinary
    assert app.state.object_service._ownership_graph_uow_factory is ownership
    assert app.state.relationship_service._uow_factory is ordinary


def test_runtime_services_remain_on_ordinary_factory_only() -> None:
    uow = _full_uow()
    ordinary = CountingFactory(uow)

    datatype = _datatype()
    datatype_version = _datatype_version(
        datatype.id,
        version=1,
        status=DataTypeVersionStatus.PUBLISHED,
    )
    template = _template()
    template_v1 = _template_version(
        template.id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(
            _property(name="hostname", datatype_id=datatype.id, datatype_version=1),
        ),
    )
    template_v2 = _template_version(
        template.id,
        version=2,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(
            _property(name="hostname", datatype_id=datatype.id, datatype_version=1),
        ),
    )
    other_template = _template(name="other")
    other_template_v1 = _template_version(
        other_template.id,
        version=1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
    )
    uow.datatypes.add(datatype)
    uow.datatypes.add_version(
        _datatype_version(
            datatype.id,
            version=1,
            status=DataTypeVersionStatus.DRAFT,
        )
    )
    uow.datatypes.replace_version(datatype_version)
    uow.object_templates.add(template)
    uow.object_templates.add(other_template)
    uow.object_templates.add_version(
        _template_version(
            template.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
            properties=template_v1.properties,
        )
    )
    uow.object_templates.replace_version(template_v1)
    uow.object_templates.add_version(
        _template_version(
            template.id,
            version=2,
            status=ObjectTemplateVersionStatus.DRAFT,
            properties=template_v2.properties,
        )
    )
    uow.object_templates.replace_version(template_v2)
    uow.object_templates.add_version(
        _template_version(other_template.id, version=1, status=ObjectTemplateVersionStatus.DRAFT)
    )
    uow.object_templates.replace_version(other_template_v1)
    created = ObjectApplicationService(
        ordinary,
        ownership_graph_uow_factory=ordinary,
    ).create_object(
        template_id=template.id,
        template_version=1,
        properties={"hostname": "router-01"},
    )
    updated = ObjectApplicationService(
        ordinary,
        ownership_graph_uow_factory=ordinary,
    ).update_object(
        object_id=created.id,
        properties={"hostname": "router-02"},
    )
    migrated = ObjectApplicationService(
        ordinary,
        ownership_graph_uow_factory=ordinary,
    ).migrate_objects(
        template_id=template.id,
        source_version=1,
        target_version=2,
        property_values={},
    )

    definition = RelationshipDefinition(
        id=uuid4(),
        source_template_id=template.id,
        target_template_id=other_template.id,
        forward_name="uses",
        reverse_name="is_used_by",
    )
    uow.relationship_definitions.add(definition)
    source = uow.objects.get(updated.id)
    assert source is not None
    target = ObjectApplicationService(
        ordinary,
        ownership_graph_uow_factory=ordinary,
    ).create_object(
        template_id=other_template.id,
        template_version=1,
        properties={},
    )
    relationship_service = RelationshipApplicationService(ordinary)
    relationship = relationship_service.create_relationship(
        relationship_definition_id=definition.id,
        source_object_id=source.id,
        target_object_id=target.id,
    )
    relationship_service.delete_relationship(relationship.id)

    assert created.id == updated.id
    assert migrated.migrated_count == 1
    assert ordinary.calls == 6


def test_structural_object_workflows_route_to_ownership_graph_factory() -> None:
    uow = _full_uow()
    ordinary = CountingFactory(uow)
    structural = CountingFactory(uow)
    service = ObjectApplicationService(
        ordinary,
        ownership_graph_uow_factory=structural,
    )

    node = _template(name="node")
    uow.object_templates.add(node)
    uow.object_templates.add_version(
        ObjectTemplateVersion(
            template_id=node.id,
            version=1,
            status=ObjectTemplateVersionStatus.DRAFT,
            components=(ObjectTemplateComponent(name="children", template_id=node.id),),
        )
    )
    uow.object_templates.replace_version(
        ObjectTemplateVersion(
            template_id=node.id,
            version=1,
            status=ObjectTemplateVersionStatus.PUBLISHED,
            components=(ObjectTemplateComponent(name="children", template_id=node.id),),
        )
    )
    root = Object(id=uuid4(), template_id=node.id, template_version=1, properties={})
    child = Object(id=uuid4(), template_id=node.id, template_version=1, properties={})
    other_parent = Object(id=uuid4(), template_id=node.id, template_version=1, properties={})
    doomed = Object(id=uuid4(), template_id=node.id, template_version=1, properties={})
    uow.objects.add(root)
    uow.objects.add(child)
    uow.objects.add(other_parent)
    uow.objects.add(doomed)

    service.attach_component(
        parent_object_id=root.id,
        slot_name="children",
        child_object_id=child.id,
    )
    service.detach_component(child.id)
    service.delete_object(doomed.id)

    assert structural.calls == 3
    assert ordinary.calls == 0

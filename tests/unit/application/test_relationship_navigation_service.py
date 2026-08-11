from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from netauto.application.relationship import RelationshipApplicationService
from netauto.application.unit_of_work import RelationshipUnitOfWork
from netauto.core.object import Object, ObjectNotFound
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateInheritanceCycle,
    ObjectTemplateParentNotFound,
    ObjectTemplateSelfInheritance,
    ObjectTemplateVersion,
    ObjectTemplateVersionNotFound,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    EffectiveRelationshipDefinition,
    Relationship,
    RelationshipDefinition,
    RelationshipDefinitionNotFound,
    RelationshipDirection,
    RelationshipNavigationView,
)
from netauto.persistence.memory.object_repository import InMemoryObjectRepository
from netauto.persistence.memory.objecttemplate_repository import (
    InMemoryObjectTemplateRepository,
)
from netauto.persistence.memory.relationship_repository import (
    InMemoryRelationshipDefinitionRepository,
    InMemoryRelationshipRepository,
)


class TrackingRelationshipRepository(InMemoryRelationshipRepository):
    def __init__(self) -> None:
        super().__init__()
        self.events: list[str] = []

    def list(self) -> tuple[Relationship, ...]:
        self.events.append("list")
        return super().list()

    def get(self, relationship_id: UUID) -> Relationship | None:
        self.events.append("get")
        return super().get(relationship_id)

    def list_incident_to_objects(
        self,
        object_ids: set[UUID],
    ) -> tuple[Relationship, ...]:
        self.events.append("list_incident_to_objects")
        return super().list_incident_to_objects(object_ids)

    def add(self, relationship: Relationship) -> None:
        self.events.append("add")
        super().add(relationship)

    def delete(self, relationship_id: UUID) -> None:
        self.events.append("delete")
        super().delete(relationship_id)


class FakeUnitOfWork(RelationshipUnitOfWork):
    def __init__(
        self,
        relationship_definitions: InMemoryRelationshipDefinitionRepository,
        relationships: TrackingRelationshipRepository,
        objects: InMemoryObjectRepository,
        object_templates: InMemoryObjectTemplateRepository,
        commit_counter: list[int],
    ) -> None:
        self._relationship_definitions = relationship_definitions
        self._relationships = relationships
        self._objects = objects
        self._object_templates = object_templates
        self._commit_counter = commit_counter

    @property
    def relationship_definitions(self) -> InMemoryRelationshipDefinitionRepository:
        return self._relationship_definitions

    @property
    def relationships(self) -> TrackingRelationshipRepository:
        return self._relationships

    @property
    def objects(self) -> InMemoryObjectRepository:
        return self._objects

    @property
    def object_templates(self) -> InMemoryObjectTemplateRepository:
        return self._object_templates

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self._commit_counter[0] += 1


def _service() -> tuple[
    RelationshipApplicationService,
    InMemoryRelationshipDefinitionRepository,
    TrackingRelationshipRepository,
    InMemoryObjectRepository,
    InMemoryObjectTemplateRepository,
    list[int],
]:
    relationship_definitions = InMemoryRelationshipDefinitionRepository()
    relationships = TrackingRelationshipRepository()
    objects = InMemoryObjectRepository()
    object_templates = InMemoryObjectTemplateRepository()
    commits = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(
            relationship_definitions,
            relationships,
            objects,
            object_templates,
            commits,
        )

    return (
        RelationshipApplicationService(factory),
        relationship_definitions,
        relationships,
        objects,
        object_templates,
        commits,
    )


def _template(
    name: str,
    *,
    template_id: UUID | None = None,
) -> ObjectTemplate:
    return ObjectTemplate(
        id=template_id or uuid4(),
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=False,
    )


def _version(
    template_id: UUID,
    version: int,
    *,
    status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.PUBLISHED,
    parent: ObjectTemplateVersionRef | None = None,
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=status,
        parent=parent,
    )


def _store_template_versions(
    repo: InMemoryObjectTemplateRepository,
    template: ObjectTemplate,
    versions: tuple[ObjectTemplateVersion, ...],
) -> None:
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


def _definition(
    *,
    source_template_id: UUID,
    target_template_id: UUID,
    forward_name: str = "uses",
    reverse_name: str = "is_used_by",
    definition_id: UUID | None = None,
) -> RelationshipDefinition:
    return RelationshipDefinition(
        id=definition_id or uuid4(),
        source_template_id=source_template_id,
        target_template_id=target_template_id,
        forward_name=forward_name,
        reverse_name=reverse_name,
    )


def _object(
    *,
    template_id: UUID,
    template_version: int,
    object_id: UUID | None = None,
) -> Object:
    return Object(
        id=object_id or uuid4(),
        template_id=template_id,
        template_version=template_version,
        properties={},
    )


def _relationship(
    *,
    relationship_definition_id: UUID,
    source_object_id: UUID,
    target_object_id: UUID,
    relationship_id: UUID | None = None,
) -> Relationship:
    return Relationship(
        id=relationship_id or uuid4(),
        relationship_definition_id=relationship_definition_id,
        source_object_id=source_object_id,
        target_object_id=target_object_id,
    )


def test_effective_relationship_definitions_missing_object_raises_without_commit() -> None:
    service, _definitions, _relationships, _objects, _templates, commits = _service()

    with pytest.raises(ObjectNotFound):
        service.list_effective_relationship_definitions(uuid4())

    assert commits[0] == 0


def test_effective_relationship_definitions_missing_exact_version_raises_without_fallback() -> None:
    service, _definitions, _relationships, objects, templates, commits = _service()
    router = _template("router")
    _store_template_versions(templates, router, (_version(router.id, 1),))
    object_value = _object(template_id=router.id, template_version=2)
    objects.add(object_value)

    with pytest.raises(ObjectTemplateVersionNotFound):
        service.list_effective_relationship_definitions(object_value.id)

    assert commits[0] == 0


def test_effective_relationship_definitions_use_exact_pinned_version_and_deprecated_pins() -> None:
    service, definitions, _relationships, objects, templates, commits = _service()
    network_device = _template("network_device")
    router = _template("router")
    credential = _template("credential")
    _store_template_versions(
        templates,
        network_device,
        (_version(network_device.id, 1),),
    )
    _store_template_versions(
        templates,
        router,
        (
            _version(router.id, 1, status=ObjectTemplateVersionStatus.DEPRECATED),
            _version(
                router.id,
                2,
                parent=ObjectTemplateVersionRef(
                    template_id=network_device.id,
                    version=1,
                ),
            ),
        ),
    )
    _store_template_versions(
        templates,
        credential,
        (_version(credential.id, 1),),
    )
    definition = _definition(
        source_template_id=network_device.id,
        target_template_id=credential.id,
    )
    definitions.add(definition)
    router_old = _object(template_id=router.id, template_version=1)
    router_new = _object(template_id=router.id, template_version=2)
    deprecated_device = _object(
        template_id=network_device.id,
        template_version=1,
        object_id=UUID(int=500),
    )
    objects.add(router_old)
    objects.add(router_new)
    objects.add(deprecated_device)

    old_effective = service.list_effective_relationship_definitions(router_old.id)
    new_effective = service.list_effective_relationship_definitions(router_new.id)
    deprecated_effective = service.list_effective_relationship_definitions(
        deprecated_device.id
    )

    assert old_effective == ()
    assert new_effective == (
        EffectiveRelationshipDefinition(
            relationship_definition_id=definition.id,
            direction=RelationshipDirection.OUTGOING,
            name="uses",
            related_template_id=credential.id,
        ),
    )
    assert deprecated_effective == (
        EffectiveRelationshipDefinition(
            relationship_definition_id=definition.id,
            direction=RelationshipDirection.OUTGOING,
            name="uses",
            related_template_id=credential.id,
        ),
    )
    assert commits[0] == 0


def test_effective_relationship_definitions_include_incoming_and_both_directions_in_order() -> None:
    service, definitions, _relationships, objects, templates, commits = _service()
    device = _template("device")
    credential = _template("credential")
    _store_template_versions(templates, device, (_version(device.id, 1),))
    _store_template_versions(templates, credential, (_version(credential.id, 1),))
    lower_id = UUID(int=1)
    higher_id = UUID(int=2)
    bidirectional = _definition(
        source_template_id=device.id,
        target_template_id=device.id,
        forward_name="connects_to",
        reverse_name="connected_from",
        definition_id=lower_id,
    )
    outgoing_only = _definition(
        source_template_id=device.id,
        target_template_id=credential.id,
        forward_name="uses",
        reverse_name="is_used_by",
        definition_id=higher_id,
    )
    definitions.add(outgoing_only)
    definitions.add(bidirectional)
    object_value = _object(template_id=device.id, template_version=1)
    objects.add(object_value)

    result = service.list_effective_relationship_definitions(object_value.id)

    assert result == (
        EffectiveRelationshipDefinition(
            relationship_definition_id=lower_id,
            direction=RelationshipDirection.OUTGOING,
            name="connects_to",
            related_template_id=device.id,
        ),
        EffectiveRelationshipDefinition(
            relationship_definition_id=lower_id,
            direction=RelationshipDirection.INCOMING,
            name="connected_from",
            related_template_id=device.id,
        ),
        EffectiveRelationshipDefinition(
            relationship_definition_id=higher_id,
            direction=RelationshipDirection.OUTGOING,
            name="uses",
            related_template_id=credential.id,
        ),
    )
    assert commits[0] == 0


def test_effective_relationship_definitions_propagate_ancestry_errors() -> None:
    service, definitions, _relationships, objects, templates, commits = _service()
    network_device = _template("network_device")
    router = _template("router")
    switch = _template("switch")
    credential = _template("credential")
    _store_template_versions(templates, network_device, (_version(network_device.id, 1),))
    _store_template_versions(templates, credential, (_version(credential.id, 1),))
    definitions.add(
        _definition(
            source_template_id=network_device.id,
            target_template_id=credential.id,
        )
    )

    missing_parent_object = _object(
        template_id=router.id,
        template_version=1,
        object_id=UUID(int=10),
    )
    cycle_object = _object(
        template_id=router.id,
        template_version=2,
        object_id=UUID(int=11),
    )
    self_object = _object(
        template_id=router.id,
        template_version=3,
        object_id=UUID(int=12),
    )
    templates.add(router)
    templates.add(switch)
    templates.add_version(
        _version(
            router.id,
            1,
            parent=ObjectTemplateVersionRef(template_id=network_device.id, version=9),
        )
    )
    templates.add_version(
        _version(
            router.id,
            2,
            parent=ObjectTemplateVersionRef(template_id=switch.id, version=1),
        )
    )
    templates.add_version(
        _version(
            switch.id,
            1,
            parent=ObjectTemplateVersionRef(template_id=router.id, version=2),
        )
    )
    templates.add_version(
        _version(
            router.id,
            3,
            parent=ObjectTemplateVersionRef(template_id=router.id, version=1),
        )
    )
    objects.add(missing_parent_object)
    objects.add(cycle_object)
    objects.add(self_object)

    with pytest.raises(ObjectTemplateParentNotFound):
        service.list_effective_relationship_definitions(missing_parent_object.id)
    with pytest.raises(ObjectTemplateInheritanceCycle):
        service.list_effective_relationship_definitions(cycle_object.id)
    with pytest.raises(ObjectTemplateSelfInheritance):
        service.list_effective_relationship_definitions(self_object.id)

    assert commits[0] == 0


def test_outgoing_and_incoming_navigation_preserve_same_physical_relationship_id() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    network_device = _template("network_device")
    credential = _template("credential")
    _store_template_versions(templates, network_device, (_version(network_device.id, 1),))
    _store_template_versions(templates, credential, (_version(credential.id, 1),))
    definition = _definition(
        source_template_id=network_device.id,
        target_template_id=credential.id,
    )
    definitions.add(definition)
    source = _object(template_id=network_device.id, template_version=1, object_id=UUID(int=101))
    target = _object(template_id=credential.id, template_version=1, object_id=UUID(int=102))
    objects.add(source)
    objects.add(target)
    relationship = _relationship(
        relationship_definition_id=definition.id,
        source_object_id=source.id,
        target_object_id=target.id,
        relationship_id=UUID(int=201),
    )
    relationships.add(relationship)
    relationships.events.clear()

    outgoing = service.list_outgoing_relationships(source.id)
    incoming = service.list_incoming_relationships(target.id)

    assert outgoing == (
        RelationshipNavigationView(
            relationship_id=relationship.id,
            relationship_definition_id=definition.id,
            source_object_id=source.id,
            target_object_id=target.id,
            direction=RelationshipDirection.OUTGOING,
            name="uses",
            related_object_id=target.id,
        ),
    )
    assert incoming == (
        RelationshipNavigationView(
            relationship_id=relationship.id,
            relationship_definition_id=definition.id,
            source_object_id=source.id,
            target_object_id=target.id,
            direction=RelationshipDirection.INCOMING,
            name="is_used_by",
            related_object_id=source.id,
        ),
    )
    assert relationships.events == [
        "list_incident_to_objects",
        "list_incident_to_objects",
    ]
    assert commits[0] == 0


def test_navigation_direction_filtering_and_neighbor_ordering() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    device = _template("device")
    credential = _template("credential")
    peer = _template("peer")
    _store_template_versions(templates, device, (_version(device.id, 1),))
    _store_template_versions(templates, credential, (_version(credential.id, 1),))
    _store_template_versions(templates, peer, (_version(peer.id, 1),))
    outgoing_definition = _definition(
        source_template_id=device.id,
        target_template_id=credential.id,
        definition_id=UUID(int=1),
    )
    incoming_definition = _definition(
        source_template_id=peer.id,
        target_template_id=device.id,
        forward_name="depends_on",
        reverse_name="depended_on_by",
        definition_id=UUID(int=2),
    )
    definitions.add(outgoing_definition)
    definitions.add(incoming_definition)
    object_value = _object(template_id=device.id, template_version=1, object_id=UUID(int=10))
    target = _object(template_id=credential.id, template_version=1, object_id=UUID(int=11))
    source = _object(template_id=peer.id, template_version=1, object_id=UUID(int=12))
    unrelated = _object(template_id=peer.id, template_version=1, object_id=UUID(int=13))
    objects.add(object_value)
    objects.add(target)
    objects.add(source)
    objects.add(unrelated)
    first_relationship = _relationship(
        relationship_definition_id=outgoing_definition.id,
        source_object_id=object_value.id,
        target_object_id=target.id,
        relationship_id=UUID(int=100),
    )
    second_relationship = _relationship(
        relationship_definition_id=incoming_definition.id,
        source_object_id=source.id,
        target_object_id=object_value.id,
        relationship_id=UUID(int=101),
    )
    unrelated_relationship = _relationship(
        relationship_definition_id=incoming_definition.id,
        source_object_id=source.id,
        target_object_id=unrelated.id,
        relationship_id=UUID(int=102),
    )
    relationships.add(first_relationship)
    relationships.add(second_relationship)
    relationships.add(unrelated_relationship)

    outgoing = service.list_outgoing_relationships(object_value.id)
    incoming = service.list_incoming_relationships(object_value.id)
    neighbors = service.list_neighbor_relationships(object_value.id)

    assert outgoing == (
        RelationshipNavigationView(
            relationship_id=first_relationship.id,
            relationship_definition_id=outgoing_definition.id,
            source_object_id=object_value.id,
            target_object_id=target.id,
            direction=RelationshipDirection.OUTGOING,
            name="uses",
            related_object_id=target.id,
        ),
    )
    assert incoming == (
        RelationshipNavigationView(
            relationship_id=second_relationship.id,
            relationship_definition_id=incoming_definition.id,
            source_object_id=source.id,
            target_object_id=object_value.id,
            direction=RelationshipDirection.INCOMING,
            name="depended_on_by",
            related_object_id=source.id,
        ),
    )
    assert neighbors == outgoing + incoming
    assert commits[0] == 0


def test_navigation_keeps_multiple_edges_to_same_neighbor_and_self_link_views() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    interface = _template("interface")
    _store_template_versions(templates, interface, (_version(interface.id, 1),))
    first_definition = _definition(
        source_template_id=interface.id,
        target_template_id=interface.id,
        forward_name="connects_to",
        reverse_name="connected_from",
        definition_id=UUID(int=1),
    )
    second_definition = _definition(
        source_template_id=interface.id,
        target_template_id=interface.id,
        forward_name="manages",
        reverse_name="managed_by",
        definition_id=UUID(int=2),
    )
    definitions.add(first_definition)
    definitions.add(second_definition)
    object_value = _object(template_id=interface.id, template_version=1, object_id=UUID(int=20))
    neighbor = _object(template_id=interface.id, template_version=1, object_id=UUID(int=21))
    objects.add(object_value)
    objects.add(neighbor)
    first_edge = _relationship(
        relationship_definition_id=first_definition.id,
        source_object_id=object_value.id,
        target_object_id=neighbor.id,
        relationship_id=UUID(int=200),
    )
    second_edge = _relationship(
        relationship_definition_id=second_definition.id,
        source_object_id=object_value.id,
        target_object_id=neighbor.id,
        relationship_id=UUID(int=201),
    )
    self_link = _relationship(
        relationship_definition_id=first_definition.id,
        source_object_id=object_value.id,
        target_object_id=object_value.id,
        relationship_id=UUID(int=202),
    )
    relationships.add(first_edge)
    relationships.add(second_edge)
    relationships.add(self_link)

    neighbors = service.list_neighbor_relationships(object_value.id)

    assert neighbors == (
        RelationshipNavigationView(
            relationship_id=first_edge.id,
            relationship_definition_id=first_definition.id,
            source_object_id=object_value.id,
            target_object_id=neighbor.id,
            direction=RelationshipDirection.OUTGOING,
            name="connects_to",
            related_object_id=neighbor.id,
        ),
        RelationshipNavigationView(
            relationship_id=second_edge.id,
            relationship_definition_id=second_definition.id,
            source_object_id=object_value.id,
            target_object_id=neighbor.id,
            direction=RelationshipDirection.OUTGOING,
            name="manages",
            related_object_id=neighbor.id,
        ),
        RelationshipNavigationView(
            relationship_id=self_link.id,
            relationship_definition_id=first_definition.id,
            source_object_id=object_value.id,
            target_object_id=object_value.id,
            direction=RelationshipDirection.OUTGOING,
            name="connects_to",
            related_object_id=object_value.id,
        ),
        RelationshipNavigationView(
            relationship_id=self_link.id,
            relationship_definition_id=first_definition.id,
            source_object_id=object_value.id,
            target_object_id=object_value.id,
            direction=RelationshipDirection.INCOMING,
            name="connected_from",
            related_object_id=object_value.id,
        ),
    )
    assert commits[0] == 0


def test_navigation_raises_on_missing_definition_corruption_without_partial_result() -> None:
    service, _definitions, relationships, objects, templates, commits = _service()
    device = _template("device")
    objects.add(_object(template_id=device.id, template_version=1, object_id=UUID(int=30)))
    _store_template_versions(templates, device, (_version(device.id, 1),))
    corrupted = _relationship(
        relationship_definition_id=UUID(int=999),
        source_object_id=UUID(int=30),
        target_object_id=UUID(int=30),
        relationship_id=UUID(int=300),
    )
    relationships.add(corrupted)

    with pytest.raises(RelationshipDefinitionNotFound):
        service.list_neighbor_relationships(UUID(int=30))

    assert commits[0] == 0


def test_navigation_missing_object_raises_without_commit() -> None:
    service, _definitions, _relationships, _objects, _templates, commits = _service()

    with pytest.raises(ObjectNotFound):
        service.list_outgoing_relationships(uuid4())
    with pytest.raises(ObjectNotFound):
        service.list_incoming_relationships(uuid4())
    with pytest.raises(ObjectNotFound):
        service.list_neighbor_relationships(uuid4())

    assert commits[0] == 0


def test_navigation_does_not_revalidate_persisted_edge_compatibility() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    network_device = _template("network_device")
    router = _template("router")
    credential = _template("credential")
    _store_template_versions(templates, network_device, (_version(network_device.id, 1),))
    _store_template_versions(
        templates,
        router,
        (
            _version(router.id, 1),
            _version(
                router.id,
                2,
                parent=ObjectTemplateVersionRef(
                    template_id=network_device.id,
                    version=1,
                ),
            ),
        ),
    )
    _store_template_versions(templates, credential, (_version(credential.id, 1),))
    definition = _definition(
        source_template_id=network_device.id,
        target_template_id=credential.id,
    )
    definitions.add(definition)
    router_object = _object(template_id=router.id, template_version=1, object_id=UUID(int=40))
    credential_object = _object(
        template_id=credential.id,
        template_version=1,
        object_id=UUID(int=41),
    )
    objects.add(router_object)
    objects.add(credential_object)
    persisted_edge = _relationship(
        relationship_definition_id=definition.id,
        source_object_id=router_object.id,
        target_object_id=credential_object.id,
        relationship_id=UUID(int=400),
    )
    relationships.add(persisted_edge)

    outgoing = service.list_outgoing_relationships(router_object.id)

    assert outgoing == (
        RelationshipNavigationView(
            relationship_id=persisted_edge.id,
            relationship_definition_id=definition.id,
            source_object_id=router_object.id,
            target_object_id=credential_object.id,
            direction=RelationshipDirection.OUTGOING,
            name="uses",
            related_object_id=credential_object.id,
        ),
    )
    assert commits[0] == 0

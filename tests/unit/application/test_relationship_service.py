from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from netauto.application.relationship import RelationshipApplicationService
from netauto.application.unit_of_work import RelationshipUnitOfWork
from netauto.core.object import Object
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
    Relationship,
    RelationshipAlreadyExists,
    RelationshipDefinition,
    RelationshipDefinitionNotFound,
    RelationshipEndpointIncompatible,
    RelationshipNotFound,
    RelationshipObjectNotFound,
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

    def get(self, relationship_id: UUID) -> Relationship | None:
        self.events.append("get")
        return super().get(relationship_id)

    def get_by_endpoints(
        self,
        relationship_definition_id: UUID,
        source_object_id: UUID,
        target_object_id: UUID,
    ) -> Relationship | None:
        self.events.append("get_by_endpoints")
        return super().get_by_endpoints(
            relationship_definition_id,
            source_object_id,
            target_object_id,
        )

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
    *,
    name: str,
    abstract: bool = False,
    template_id: UUID | None = None,
) -> ObjectTemplate:
    return ObjectTemplate(
        id=template_id or uuid4(),
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=abstract,
    )


def _version(
    template_id: UUID,
    *,
    version: int,
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
) -> RelationshipDefinition:
    return RelationshipDefinition(
        id=uuid4(),
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


def _store_object(repo: InMemoryObjectRepository, object_value: Object) -> None:
    repo.add(object_value)


def test_successful_exact_template_source_and_target() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    source_template = _template(name="network_device")
    target_template = _template(name="credential")
    _store_template_versions(templates, source_template, (_version(source_template.id, version=1),))
    _store_template_versions(templates, target_template, (_version(target_template.id, version=1),))
    definition = _definition(
        source_template_id=source_template.id,
        target_template_id=target_template.id,
    )
    definitions.add(definition)
    source_object = _object(template_id=source_template.id, template_version=1)
    target_object = _object(template_id=target_template.id, template_version=1)
    _store_object(objects, source_object)
    _store_object(objects, target_object)

    created = service.create_relationship(
        relationship_definition_id=definition.id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )

    assert created.relationship_definition_id == definition.id
    assert created.source_object_id == source_object.id
    assert created.target_object_id == target_object.id
    assert relationships.get(created.id) == created
    assert relationships.events == ["get_by_endpoints", "add", "get"]
    assert commits[0] == 1


def test_successful_inherited_source() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    source_ancestor = _template(name="network_device")
    source_child = _template(name="router")
    target_template = _template(name="credential")
    _store_template_versions(templates, source_ancestor, (_version(source_ancestor.id, version=1),))
    _store_template_versions(
        templates,
        source_child,
        (
            _version(
                source_child.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=source_ancestor.id, version=1),
            ),
        ),
    )
    _store_template_versions(templates, target_template, (_version(target_template.id, version=1),))
    definition = _definition(
        source_template_id=source_ancestor.id,
        target_template_id=target_template.id,
    )
    definitions.add(definition)
    source_object = _object(template_id=source_child.id, template_version=1)
    target_object = _object(template_id=target_template.id, template_version=1)
    _store_object(objects, source_object)
    _store_object(objects, target_object)

    created = service.create_relationship(
        relationship_definition_id=definition.id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )

    assert relationships.get(created.id) == created
    assert commits[0] == 1


def test_successful_inherited_target_and_both_endpoints_inherited() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    source_ancestor = _template(name="network_device")
    source_child = _template(name="router")
    target_ancestor = _template(name="credential")
    target_child = _template(name="tacacs_credential")
    _store_template_versions(templates, source_ancestor, (_version(source_ancestor.id, version=1),))
    _store_template_versions(
        templates,
        source_child,
        (
            _version(
                source_child.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=source_ancestor.id, version=1),
            ),
        ),
    )
    _store_template_versions(templates, target_ancestor, (_version(target_ancestor.id, version=1),))
    _store_template_versions(
        templates,
        target_child,
        (
            _version(
                target_child.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=target_ancestor.id, version=1),
            ),
        ),
    )
    definition = _definition(
        source_template_id=source_ancestor.id,
        target_template_id=target_ancestor.id,
    )
    definitions.add(definition)
    source_object = _object(template_id=source_child.id, template_version=1)
    target_object = _object(template_id=target_child.id, template_version=1)
    _store_object(objects, source_object)
    _store_object(objects, target_object)

    created = service.create_relationship(
        relationship_definition_id=definition.id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )

    assert relationships.get(created.id) == created
    assert commits[0] == 1


def test_incompatible_source_and_target_are_rejected_before_mutation() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    source_required = _template(name="network_device")
    source_actual = _template(name="router")
    target_required = _template(name="credential")
    target_actual = _template(name="password")
    for template in (source_required, source_actual, target_required, target_actual):
        _store_template_versions(templates, template, (_version(template.id, version=1),))
    definition = _definition(
        source_template_id=source_required.id,
        target_template_id=target_required.id,
    )
    definitions.add(definition)
    bad_source = _object(template_id=source_actual.id, template_version=1)
    bad_target = _object(template_id=target_actual.id, template_version=1)
    good_source = _object(template_id=source_required.id, template_version=1)
    good_target = _object(template_id=target_required.id, template_version=1)
    _store_object(objects, bad_source)
    _store_object(objects, bad_target)
    _store_object(objects, good_source)
    _store_object(objects, good_target)

    with pytest.raises(RelationshipEndpointIncompatible):
        service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=bad_source.id,
            target_object_id=good_target.id,
        )
    with pytest.raises(RelationshipEndpointIncompatible):
        service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=good_source.id,
            target_object_id=bad_target.id,
        )

    assert relationships.events == []
    assert commits[0] == 0


def test_missing_definition_source_and_target_object_are_rejected() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    source_template = _template(name="network_device")
    target_template = _template(name="credential")
    _store_template_versions(templates, source_template, (_version(source_template.id, version=1),))
    _store_template_versions(templates, target_template, (_version(target_template.id, version=1),))
    definition = _definition(
        source_template_id=source_template.id,
        target_template_id=target_template.id,
    )
    definitions.add(definition)
    source_object = _object(template_id=source_template.id, template_version=1)
    target_object = _object(template_id=target_template.id, template_version=1)
    _store_object(objects, source_object)
    _store_object(objects, target_object)

    with pytest.raises(RelationshipDefinitionNotFound):
        service.create_relationship(
            relationship_definition_id=uuid4(),
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )
    with pytest.raises(RelationshipObjectNotFound):
        service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=uuid4(),
            target_object_id=target_object.id,
        )
    with pytest.raises(RelationshipObjectNotFound):
        service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=source_object.id,
            target_object_id=uuid4(),
        )

    assert relationships.events == []
    assert commits[0] == 0


def test_historical_exact_pin_distinction_and_deprecated_pinned_object() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    network_device = _template(name="network_device")
    router = _template(name="router")
    credential = _template(name="credential")
    _store_template_versions(
        templates,
        network_device,
        (
            _version(
                network_device.id,
                version=1,
                status=ObjectTemplateVersionStatus.DEPRECATED,
            ),
        ),
    )
    _store_template_versions(
        templates,
        router,
        (
            _version(
                router.id,
                version=1,
                status=ObjectTemplateVersionStatus.DEPRECATED,
            ),
            _version(
                router.id,
                version=2,
                parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
            ),
        ),
    )
    _store_template_versions(templates, credential, (_version(credential.id, version=1),))
    definition = _definition(
        source_template_id=network_device.id,
        target_template_id=credential.id,
    )
    definitions.add(definition)
    router_old = _object(template_id=router.id, template_version=1)
    router_new = _object(template_id=router.id, template_version=2)
    credential_object = _object(template_id=credential.id, template_version=1)
    deprecated_network_device_object = _object(
        template_id=network_device.id,
        template_version=1,
    )
    _store_object(objects, router_old)
    _store_object(objects, router_new)
    _store_object(objects, credential_object)
    _store_object(objects, deprecated_network_device_object)

    with pytest.raises(RelationshipEndpointIncompatible):
        service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=router_old.id,
            target_object_id=credential_object.id,
        )

    created_from_deprecated_exact = service.create_relationship(
        relationship_definition_id=definition.id,
        source_object_id=deprecated_network_device_object.id,
        target_object_id=credential_object.id,
    )
    created = service.create_relationship(
        relationship_definition_id=definition.id,
        source_object_id=router_new.id,
        target_object_id=credential_object.id,
    )

    assert relationships.get(created_from_deprecated_exact.id) == created_from_deprecated_exact
    assert relationships.get(created.id) == created
    assert commits[0] == 2


def test_missing_exact_pinned_version_and_structural_ancestry_errors_propagate() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    source_required = _template(name="network_device")
    source_actual = _template(name="router")
    target_template = _template(name="credential")
    _store_template_versions(templates, source_required, (_version(source_required.id, version=1),))
    _store_template_versions(templates, target_template, (_version(target_template.id, version=1),))
    definition = _definition(
        source_template_id=source_required.id,
        target_template_id=target_template.id,
    )
    definitions.add(definition)
    missing_version_object = _object(template_id=source_actual.id, template_version=99)
    target_object = _object(template_id=target_template.id, template_version=1)
    _store_object(objects, missing_version_object)
    _store_object(objects, target_object)

    with pytest.raises(ObjectTemplateVersionNotFound):
        service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=missing_version_object.id,
            target_object_id=target_object.id,
        )

    bad_parent = _template(name="broken_router")
    _store_template_versions(
        templates,
        bad_parent,
        (
            _version(
                bad_parent.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
            ),
        ),
    )
    bad_parent_object = _object(template_id=bad_parent.id, template_version=1)
    _store_object(objects, bad_parent_object)

    with pytest.raises(ObjectTemplateParentNotFound):
        service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=bad_parent_object.id,
            target_object_id=target_object.id,
        )

    self_inheriting = _template(name="self_inheriting")
    _store_template_versions(
        templates,
        self_inheriting,
        (
            _version(
                self_inheriting.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=self_inheriting.id, version=2),
            ),
            _version(self_inheriting.id, version=2),
        ),
    )
    self_object = _object(template_id=self_inheriting.id, template_version=1)
    _store_object(objects, self_object)

    with pytest.raises(ObjectTemplateSelfInheritance):
        service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=self_object.id,
            target_object_id=target_object.id,
        )

    cyclic_a = _template(name="cyclic_a")
    cyclic_b = _template(name="cyclic_b")
    _store_template_versions(
        templates,
        cyclic_a,
        (
            _version(
                cyclic_a.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=cyclic_b.id, version=1),
            ),
        ),
    )
    _store_template_versions(
        templates,
        cyclic_b,
        (
            _version(
                cyclic_b.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=cyclic_a.id, version=1),
            ),
        ),
    )
    cyclic_object = _object(template_id=cyclic_a.id, template_version=1)
    _store_object(objects, cyclic_object)

    with pytest.raises(ObjectTemplateInheritanceCycle):
        service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=cyclic_object.id,
            target_object_id=target_object.id,
        )

    assert "add" not in relationships.events
    assert commits[0] == 0


def test_duplicate_canonical_edge_rejected_and_same_pair_different_definitions_allowed() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    template = _template(name="interface")
    _store_template_versions(templates, template, (_version(template.id, version=1),))
    definition = _definition(
        source_template_id=template.id,
        target_template_id=template.id,
        forward_name="connects_to",
        reverse_name="connects_to",
    )
    other_definition = _definition(
        source_template_id=template.id,
        target_template_id=template.id,
        forward_name="monitors",
        reverse_name="monitored_by",
    )
    definitions.add(definition)
    definitions.add(other_definition)
    source_object = _object(template_id=template.id, template_version=1)
    target_object = _object(template_id=template.id, template_version=1)
    _store_object(objects, source_object)
    _store_object(objects, target_object)

    first = service.create_relationship(
        relationship_definition_id=definition.id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )

    with pytest.raises(RelationshipAlreadyExists):
        service.create_relationship(
            relationship_definition_id=definition.id,
            source_object_id=source_object.id,
            target_object_id=target_object.id,
        )

    second = service.create_relationship(
        relationship_definition_id=other_definition.id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )

    assert first.relationship_definition_id != second.relationship_definition_id
    assert relationships.events.count("add") == 2
    assert commits[0] == 2


def test_same_template_relationship_and_self_link_allowed() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    template = _template(name="interface")
    _store_template_versions(templates, template, (_version(template.id, version=1),))
    definition = _definition(
        source_template_id=template.id,
        target_template_id=template.id,
        forward_name="connects_to",
        reverse_name="connects_to",
    )
    definitions.add(definition)
    object_value = _object(template_id=template.id, template_version=1)
    _store_object(objects, object_value)

    created = service.create_relationship(
        relationship_definition_id=definition.id,
        source_object_id=object_value.id,
        target_object_id=object_value.id,
    )

    assert created.source_object_id == created.target_object_id
    assert relationships.get(created.id) == created
    assert commits[0] == 1


def test_list_get_and_delete_are_read_only_or_commit_once() -> None:
    service, definitions, relationships, objects, templates, commits = _service()
    source_template = _template(name="network_device")
    target_template = _template(name="credential")
    _store_template_versions(templates, source_template, (_version(source_template.id, version=1),))
    _store_template_versions(templates, target_template, (_version(target_template.id, version=1),))
    definition = _definition(
        source_template_id=source_template.id,
        target_template_id=target_template.id,
    )
    definitions.add(definition)
    source_object = _object(template_id=source_template.id, template_version=1)
    target_object = _object(template_id=target_template.id, template_version=1)
    _store_object(objects, source_object)
    _store_object(objects, target_object)
    created = service.create_relationship(
        relationship_definition_id=definition.id,
        source_object_id=source_object.id,
        target_object_id=target_object.id,
    )
    relationships.events.clear()
    commits[0] = 0

    assert service.list_relationships() == (created,)
    assert service.get_relationship(created.id) == created
    assert commits[0] == 0

    service.delete_relationship(created.id)

    assert relationships.events == ["get", "get", "delete"]
    assert commits[0] == 1

    with pytest.raises(RelationshipNotFound):
        service.delete_relationship(created.id)
    assert commits[0] == 1

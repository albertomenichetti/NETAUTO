from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from netauto.application.relationship import RelationshipDefinitionApplicationService
from netauto.application.unit_of_work import RelationshipDefinitionUnitOfWork
from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateInheritanceCycle,
    ObjectTemplateParentNotFound,
    ObjectTemplateSelfInheritance,
    ObjectTemplateVersion,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.core.relationship import (
    Relationship,
    RelationshipDefinition,
    RelationshipDefinitionInUse,
    RelationshipDefinitionNotFound,
    RelationshipDefinitionSemanticConflict,
    RelationshipDefinitionTemplateNotFound,
    RelationshipDefinitionTemplateNotPublished,
)
from netauto.persistence.memory.objecttemplate_repository import (
    InMemoryObjectTemplateRepository,
)
from netauto.persistence.memory.relationship_repository import (
    InMemoryRelationshipDefinitionRepository,
    InMemoryRelationshipRepository,
)


class TrackingRelationshipDefinitionRepository(InMemoryRelationshipDefinitionRepository):
    def __init__(self) -> None:
        super().__init__()
        self.events: list[str] = []

    def list(self) -> tuple[RelationshipDefinition, ...]:
        self.events.append("list")
        return super().list()

    def add(self, definition: RelationshipDefinition) -> None:
        self.events.append("add")
        super().add(definition)

    def delete(self, definition_id: UUID) -> None:
        self.events.append("delete")
        super().delete(definition_id)


class FakeUnitOfWork(RelationshipDefinitionUnitOfWork):
    def __init__(
        self,
        object_templates: InMemoryObjectTemplateRepository,
        relationship_definitions: TrackingRelationshipDefinitionRepository,
        relationships: InMemoryRelationshipRepository,
        commit_counter: list[int],
    ) -> None:
        self._object_templates = object_templates
        self._relationship_definitions = relationship_definitions
        self._relationships = relationships
        self._commit_counter = commit_counter

    @property
    def object_templates(self) -> InMemoryObjectTemplateRepository:
        return self._object_templates

    @property
    def relationship_definitions(self) -> TrackingRelationshipDefinitionRepository:
        return self._relationship_definitions

    @property
    def relationships(self) -> InMemoryRelationshipRepository:
        return self._relationships

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self._commit_counter[0] += 1


def _service() -> tuple[
    RelationshipDefinitionApplicationService,
    InMemoryObjectTemplateRepository,
    TrackingRelationshipDefinitionRepository,
    InMemoryRelationshipRepository,
    list[int],
]:
    object_templates = InMemoryObjectTemplateRepository()
    relationship_definitions = TrackingRelationshipDefinitionRepository()
    relationships = InMemoryRelationshipRepository()
    commits = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(
            object_templates,
            relationship_definitions,
            relationships,
            commits,
        )

    return (
        RelationshipDefinitionApplicationService(
            factory,
            model_write_uow_factory=factory,
        ),
        object_templates,
        relationship_definitions,
        relationships,
        commits,
    )


def _template(
    *,
    namespace: str = "network",
    name: str = "device",
    abstract: bool = False,
    template_id: UUID | None = None,
) -> ObjectTemplate:
    return ObjectTemplate(
        id=template_id or uuid4(),
        namespace=namespace,
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


def _relationship(
    *,
    relationship_definition_id: UUID,
    source_object_id: UUID | None = None,
    target_object_id: UUID | None = None,
) -> Relationship:
    return Relationship(
        id=uuid4(),
        relationship_definition_id=relationship_definition_id,
        source_object_id=source_object_id or uuid4(),
        target_object_id=target_object_id or uuid4(),
    )


def test_list_relationship_definitions() -> None:
    service, object_templates, relationship_definitions, _relationships, _commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(object_templates, source, ())
    _store_template_versions(object_templates, target, ())
    first = _definition(source_template_id=source.id, target_template_id=target.id)
    second = _definition(
        source_template_id=target.id,
        target_template_id=source.id,
        forward_name="manages",
        reverse_name="managed_by",
    )
    relationship_definitions.add(first)
    relationship_definitions.add(second)
    relationship_definitions.events.clear()

    assert service.list_relationship_definitions() == tuple(
        sorted((first, second), key=lambda item: str(item.id))
    )


def test_get_existing_relationship_definition() -> None:
    service, object_templates, relationship_definitions, _relationships, _commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(object_templates, source, ())
    _store_template_versions(object_templates, target, ())
    definition = _definition(source_template_id=source.id, target_template_id=target.id)
    relationship_definitions.add(definition)
    relationship_definitions.events.clear()

    assert service.get_relationship_definition(definition.id) == definition


def test_get_missing_relationship_definition_raises_not_found() -> None:
    service, _templates, _definitions, _relationships, _commits = _service()

    with pytest.raises(RelationshipDefinitionNotFound):
        service.get_relationship_definition(uuid4())


def test_create_relationship_definition_exact_endpoints() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))

    created = service.create_relationship_definition(
        source_template_id=source.id,
        target_template_id=target.id,
        forward_name="uses",
        reverse_name="is_used_by",
    )

    assert created.source_template_id == source.id
    assert created.target_template_id == target.id
    assert created.forward_name == "uses"
    assert created.reverse_name == "is_used_by"
    assert relationship_definitions.get(created.id) == created
    assert relationship_definitions.events == ["list", "add"]
    assert commits[0] == 1


def test_missing_source_template_rejected() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    target = _template(name="target")
    _store_template_versions(object_templates, target, ())

    with pytest.raises(RelationshipDefinitionTemplateNotFound):
        service.create_relationship_definition(
            source_template_id=uuid4(),
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == []
    assert commits[0] == 0


def test_missing_target_template_rejected() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))

    with pytest.raises(RelationshipDefinitionTemplateNotFound):
        service.create_relationship_definition(
            source_template_id=source.id,
            target_template_id=uuid4(),
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == []
    assert commits[0] == 0


def test_same_template_definition_is_allowed() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    template = _template(name="device")
    _store_template_versions(object_templates, template, (_version(template.id, version=1),))

    created = service.create_relationship_definition(
        source_template_id=template.id,
        target_template_id=template.id,
        forward_name="connects_to",
        reverse_name="connects_to",
    )

    assert relationship_definitions.get(created.id) == created
    assert commits[0] == 1


def test_abstract_endpoint_is_accepted() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="device", abstract=True)
    target = _template(name="credential")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))

    created = service.create_relationship_definition(
        source_template_id=source.id,
        target_template_id=target.id,
        forward_name="uses",
        reverse_name="is_used_by",
    )

    assert relationship_definitions.get(created.id) == created
    assert commits[0] == 1


def test_exact_canonical_duplicate_rejected_without_commit() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    existing = _definition(source_template_id=source.id, target_template_id=target.id)
    relationship_definitions.add(existing)
    relationship_definitions.events.clear()

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.create_relationship_definition(
            source_template_id=source.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == ["list"]
    assert commits[0] == 0

def test_source_with_only_draft_versions_is_rejected_before_mutation() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(
        object_templates,
        source,
        (_version(source.id, version=1, status=ObjectTemplateVersionStatus.DRAFT),),
    )
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))

    with pytest.raises(RelationshipDefinitionTemplateNotPublished):
        service.create_relationship_definition(
            source_template_id=source.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == []
    assert commits[0] == 0


def test_target_with_only_draft_versions_is_rejected_before_mutation() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(
        object_templates,
        target,
        (_version(target.id, version=1, status=ObjectTemplateVersionStatus.DRAFT),),
    )

    with pytest.raises(RelationshipDefinitionTemplateNotPublished):
        service.create_relationship_definition(
            source_template_id=source.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == []
    assert commits[0] == 0


def test_source_with_only_deprecated_versions_is_rejected_before_mutation() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(
        object_templates,
        source,
        (
            _version(
                source.id,
                version=1,
                status=ObjectTemplateVersionStatus.DEPRECATED,
            ),
        ),
    )
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))

    with pytest.raises(RelationshipDefinitionTemplateNotPublished):
        service.create_relationship_definition(
            source_template_id=source.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == []
    assert commits[0] == 0


def test_target_with_only_deprecated_versions_is_rejected_before_mutation() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(
        object_templates,
        target,
        (
            _version(
                target.id,
                version=1,
                status=ObjectTemplateVersionStatus.DEPRECATED,
            ),
        ),
    )

    with pytest.raises(RelationshipDefinitionTemplateNotPublished):
        service.create_relationship_definition(
            source_template_id=source.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == []
    assert commits[0] == 0


def test_draft_and_deprecated_without_published_is_rejected() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(
        object_templates,
        source,
        (
            _version(source.id, version=1, status=ObjectTemplateVersionStatus.DRAFT),
            _version(
                source.id,
                version=2,
                status=ObjectTemplateVersionStatus.DEPRECATED,
            ),
        ),
    )
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))

    with pytest.raises(RelationshipDefinitionTemplateNotPublished):
        service.create_relationship_definition(
            source_template_id=source.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == []
    assert commits[0] == 0


def test_endpoint_with_at_least_one_published_version_is_accepted() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(
        object_templates,
        source,
        (
            _version(source.id, version=1, status=ObjectTemplateVersionStatus.DRAFT),
            _version(source.id, version=2, status=ObjectTemplateVersionStatus.PUBLISHED),
            _version(
                source.id,
                version=3,
                status=ObjectTemplateVersionStatus.DEPRECATED,
            ),
        ),
    )
    _store_template_versions(
        object_templates,
        target,
        (
            _version(target.id, version=1, status=ObjectTemplateVersionStatus.DEPRECATED),
            _version(target.id, version=2, status=ObjectTemplateVersionStatus.PUBLISHED),
        ),
    )

    created = service.create_relationship_definition(
        source_template_id=source.id,
        target_template_id=target.id,
        forward_name="uses",
        reverse_name="is_used_by",
    )

    assert relationship_definitions.get(created.id) == created
    assert relationship_definitions.events == ["list", "add"]
    assert commits[0] == 1


def test_inverse_canonical_duplicate_rejected_without_commit() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    existing = _definition(source_template_id=source.id, target_template_id=target.id)
    relationship_definitions.add(existing)
    relationship_definitions.events.clear()

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.create_relationship_definition(
            source_template_id=target.id,
            target_template_id=source.id,
            forward_name="is_used_by",
            reverse_name="uses",
        )

    assert relationship_definitions.events == ["list"]
    assert commits[0] == 0


def test_source_ancestor_descendant_conflict_is_rejected() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    source_child = _template(name="source_child")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(
        object_templates,
        source_child,
        (
            _version(
                source_child.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=source.id, version=1),
            ),
        ),
    )
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    relationship_definitions.add(
        _definition(source_template_id=source.id, target_template_id=target.id)
    )
    relationship_definitions.events.clear()

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.create_relationship_definition(
            source_template_id=source_child.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == ["list"]
    assert commits[0] == 0


def test_existing_child_then_later_ancestor_conflict_is_rejected() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    source_child = _template(name="source_child")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(
        object_templates,
        source_child,
        (
            _version(
                source_child.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=source.id, version=1),
            ),
        ),
    )
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    relationship_definitions.add(
        _definition(source_template_id=source_child.id, target_template_id=target.id)
    )
    relationship_definitions.events.clear()

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.create_relationship_definition(
            source_template_id=source.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == ["list"]
    assert commits[0] == 0


def test_target_ancestor_descendant_conflict_is_rejected() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    target_child = _template(name="target_child")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    _store_template_versions(
        object_templates,
        target_child,
        (
            _version(
                target_child.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=target.id, version=1),
            ),
        ),
    )
    relationship_definitions.add(
        _definition(source_template_id=source.id, target_template_id=target.id)
    )
    relationship_definitions.events.clear()

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.create_relationship_definition(
            source_template_id=source.id,
            target_template_id=target_child.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == ["list"]
    assert commits[0] == 0


def test_both_endpoint_overlaps_are_rejected() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    source_child = _template(name="source_child")
    target = _template(name="target")
    target_child = _template(name="target_child")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(
        object_templates,
        source_child,
        (
            _version(
                source_child.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=source.id, version=1),
            ),
        ),
    )
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    _store_template_versions(
        object_templates,
        target_child,
        (
            _version(
                target_child.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=target.id, version=1),
            ),
        ),
    )
    relationship_definitions.add(
        _definition(source_template_id=source_child.id, target_template_id=target_child.id)
    )
    relationship_definitions.events.clear()

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.create_relationship_definition(
            source_template_id=source.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == ["list"]
    assert commits[0] == 0


def test_non_overlapping_source_is_allowed() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    unrelated = _template(name="unrelated")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(object_templates, unrelated, (_version(unrelated.id, version=1),))
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    relationship_definitions.add(
        _definition(source_template_id=source.id, target_template_id=target.id)
    )
    relationship_definitions.events.clear()

    created = service.create_relationship_definition(
        source_template_id=unrelated.id,
        target_template_id=target.id,
        forward_name="uses",
        reverse_name="is_used_by",
    )

    assert relationship_definitions.get(created.id) == created
    assert relationship_definitions.events == ["list", "add"]
    assert commits[0] == 1


def test_non_overlapping_target_is_allowed() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    unrelated = _template(name="unrelated")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    _store_template_versions(object_templates, unrelated, (_version(unrelated.id, version=1),))
    relationship_definitions.add(
        _definition(source_template_id=source.id, target_template_id=target.id)
    )
    relationship_definitions.events.clear()

    created = service.create_relationship_definition(
        source_template_id=source.id,
        target_template_id=unrelated.id,
        forward_name="uses",
        reverse_name="is_used_by",
    )

    assert relationship_definitions.get(created.id) == created
    assert relationship_definitions.events == ["list", "add"]
    assert commits[0] == 1


def test_different_semantics_are_allowed() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    relationship_definitions.add(
        _definition(source_template_id=source.id, target_template_id=target.id)
    )
    relationship_definitions.events.clear()

    created = service.create_relationship_definition(
        source_template_id=source.id,
        target_template_id=target.id,
        forward_name="manages",
        reverse_name="managed_by",
    )

    assert relationship_definitions.get(created.id) == created
    assert relationship_definitions.events == ["list", "add"]
    assert commits[0] == 1


def test_symmetric_semantic_names_conflict_when_any_alignment_overlaps() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    source_child = _template(name="source_child")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(
        object_templates,
        source_child,
        (
            _version(
                source_child.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=source.id, version=1),
            ),
        ),
    )
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    relationship_definitions.add(
        _definition(
            source_template_id=source.id,
            target_template_id=target.id,
            forward_name="connects_to",
            reverse_name="connects_to",
        )
    )
    relationship_definitions.events.clear()

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.create_relationship_definition(
            source_template_id=target.id,
            target_template_id=source_child.id,
            forward_name="connects_to",
            reverse_name="connects_to",
        )

    assert relationship_definitions.events == ["list"]
    assert commits[0] == 0


def test_deprecated_only_overlap_participates_in_conflict_detection() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    source_child = _template(name="source_child")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(
        object_templates,
        source_child,
        (
            _version(source_child.id, version=1, status=ObjectTemplateVersionStatus.PUBLISHED),
            _version(
                source_child.id,
                version=2,
                status=ObjectTemplateVersionStatus.DEPRECATED,
                parent=ObjectTemplateVersionRef(template_id=source.id, version=1),
            ),
        ),
    )
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    relationship_definitions.add(
        _definition(source_template_id=source.id, target_template_id=target.id)
    )
    relationship_definitions.events.clear()

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.create_relationship_definition(
            source_template_id=source_child.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == ["list"]
    assert commits[0] == 0


def test_draft_only_overlap_does_not_block_creation() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    source_child = _template(name="source_child")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(
        object_templates,
        source_child,
        (
            _version(source_child.id, version=1, status=ObjectTemplateVersionStatus.PUBLISHED),
            _version(
                source_child.id,
                version=2,
                status=ObjectTemplateVersionStatus.DRAFT,
                parent=ObjectTemplateVersionRef(template_id=source.id, version=1),
            ),
        ),
    )
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    relationship_definitions.add(
        _definition(source_template_id=source.id, target_template_id=target.id)
    )
    relationship_definitions.events.clear()

    created = service.create_relationship_definition(
        source_template_id=source_child.id,
        target_template_id=target.id,
        forward_name="uses",
        reverse_name="is_used_by",
    )

    assert relationship_definitions.get(created.id) == created
    assert relationship_definitions.events == ["list", "add"]
    assert commits[0] == 1


@pytest.mark.parametrize(
    "historical_status",
    [
        ObjectTemplateVersionStatus.PUBLISHED,
        ObjectTemplateVersionStatus.DEPRECATED,
    ],
)
def test_historical_exact_version_ancestry_conflict_uses_published_and_deprecated_versions(
    historical_status: ObjectTemplateVersionStatus,
) -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    network_device = _template(name="network_device")
    router = _template(name="router")
    credential = _template(name="credential")
    nd_v1 = _version(network_device.id, version=1)
    _store_template_versions(object_templates, network_device, (nd_v1,))
    _store_template_versions(
        object_templates,
        router,
        (
            _version(
                router.id,
                version=1,
                status=historical_status,
                parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
            ),
            _version(router.id, version=2),
        ),
    )
    _store_template_versions(object_templates, credential, (_version(credential.id, version=1),))
    relationship_definitions.add(
        _definition(
            source_template_id=network_device.id,
            target_template_id=credential.id,
        )
    )
    relationship_definitions.events.clear()

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.create_relationship_definition(
            source_template_id=router.id,
            target_template_id=credential.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == ["list"]
    assert commits[0] == 0


def test_missing_parent_in_usable_ancestry_propagates_error() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    broken = _template(name="broken")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(
        object_templates,
        broken,
        (
            _version(
                broken.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=source.id, version=99),
            ),
        ),
    )
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    relationship_definitions.add(
        _definition(source_template_id=source.id, target_template_id=target.id)
    )
    relationship_definitions.events.clear()

    with pytest.raises(ObjectTemplateParentNotFound):
        service.create_relationship_definition(
            source_template_id=broken.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == ["list"]
    assert commits[0] == 0


def test_self_inheritance_in_usable_ancestry_propagates_error() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    broken = _template(name="broken")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(
        object_templates,
        broken,
        (
            _version(
                broken.id,
                version=2,
                parent=ObjectTemplateVersionRef(template_id=broken.id, version=1),
            ),
        ),
    )
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    relationship_definitions.add(
        _definition(source_template_id=source.id, target_template_id=target.id)
    )
    relationship_definitions.events.clear()

    with pytest.raises(ObjectTemplateSelfInheritance):
        service.create_relationship_definition(
            source_template_id=broken.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == ["list"]
    assert commits[0] == 0


def test_cycle_in_usable_ancestry_propagates_error() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    left = _template(name="left")
    right = _template(name="right")
    target = _template(name="target")
    _store_template_versions(object_templates, source, (_version(source.id, version=1),))
    _store_template_versions(
        object_templates,
        left,
        (
            _version(
                left.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=right.id, version=1),
            ),
        ),
    )
    _store_template_versions(
        object_templates,
        right,
        (
            _version(
                right.id,
                version=1,
                parent=ObjectTemplateVersionRef(template_id=left.id, version=1),
            ),
        ),
    )
    _store_template_versions(object_templates, target, (_version(target.id, version=1),))
    relationship_definitions.add(
        _definition(source_template_id=source.id, target_template_id=target.id)
    )
    relationship_definitions.events.clear()

    with pytest.raises(ObjectTemplateInheritanceCycle):
        service.create_relationship_definition(
            source_template_id=left.id,
            target_template_id=target.id,
            forward_name="uses",
            reverse_name="is_used_by",
        )

    assert relationship_definitions.events == ["list"]
    assert commits[0] == 0


def test_delete_existing_definition_commits_once() -> None:
    service, object_templates, relationship_definitions, _relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(object_templates, source, ())
    _store_template_versions(object_templates, target, ())
    definition = _definition(source_template_id=source.id, target_template_id=target.id)
    relationship_definitions.add(definition)
    relationship_definitions.events.clear()

    service.delete_relationship_definition(definition.id)

    assert relationship_definitions.get(definition.id) is None
    assert relationship_definitions.events == ["delete"]
    assert commits[0] == 1


def test_delete_missing_definition_does_not_commit() -> None:
    service, _templates, relationship_definitions, _relationships, commits = _service()

    with pytest.raises(RelationshipDefinitionNotFound):
        service.delete_relationship_definition(uuid4())

    assert relationship_definitions.events == []
    assert commits[0] == 0


def test_delete_definition_in_use_is_rejected_without_commit() -> None:
    service, object_templates, relationship_definitions, relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(object_templates, source, ())
    _store_template_versions(object_templates, target, ())
    definition = _definition(source_template_id=source.id, target_template_id=target.id)
    relationship_definitions.add(definition)
    runtime_relationship = _relationship(relationship_definition_id=definition.id)
    relationships.add(runtime_relationship)
    relationship_definitions.events.clear()

    with pytest.raises(RelationshipDefinitionInUse):
        service.delete_relationship_definition(definition.id)

    assert relationship_definitions.get(definition.id) == definition
    assert relationships.get(runtime_relationship.id) == runtime_relationship
    assert relationship_definitions.events == []
    assert commits[0] == 0


def test_delete_definition_with_multiple_runtime_relationships_is_rejected() -> None:
    service, object_templates, relationship_definitions, relationships, commits = _service()
    source = _template(name="source")
    target = _template(name="target")
    _store_template_versions(object_templates, source, ())
    _store_template_versions(object_templates, target, ())
    definition = _definition(source_template_id=source.id, target_template_id=target.id)
    other_definition = _definition(
        source_template_id=source.id,
        target_template_id=target.id,
        forward_name="manages",
        reverse_name="managed_by",
    )
    relationship_definitions.add(definition)
    relationship_definitions.add(other_definition)
    first = _relationship(relationship_definition_id=definition.id)
    second = _relationship(relationship_definition_id=definition.id)
    unrelated = _relationship(relationship_definition_id=other_definition.id)
    relationships.add(first)
    relationships.add(second)
    relationships.add(unrelated)
    relationship_definitions.events.clear()

    with pytest.raises(RelationshipDefinitionInUse):
        service.delete_relationship_definition(definition.id)

    assert relationship_definitions.get(definition.id) == definition
    assert relationship_definitions.get(other_definition.id) == other_definition
    assert relationships.get(first.id) == first
    assert relationships.get(second.id) == second
    assert relationships.get(unrelated.id) == unrelated
    assert relationship_definitions.events == []
    assert commits[0] == 0

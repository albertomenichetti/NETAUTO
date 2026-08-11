from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from netauto.application.objecttemplate import ObjectTemplateApplicationService
from netauto.application.unit_of_work import ObjectTemplateUnitOfWork
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
    RelationshipDefinition,
    RelationshipDefinitionSemanticConflict,
)
from netauto.persistence.memory.datatype_repository import InMemoryDataTypeRepository
from netauto.persistence.memory.object_repository import InMemoryObjectRepository
from netauto.persistence.memory.objecttemplate_repository import (
    InMemoryObjectTemplateRepository,
)
from netauto.persistence.memory.relationship_repository import (
    InMemoryRelationshipDefinitionRepository,
)


class TrackingObjectTemplateRepository(InMemoryObjectTemplateRepository):
    def __init__(self) -> None:
        super().__init__()
        self.replace_version_calls: list[ObjectTemplateVersion] = []

    def replace_version(self, version: ObjectTemplateVersion) -> None:
        self.replace_version_calls.append(version)
        super().replace_version(version)


class TrackingRelationshipDefinitionRepository(InMemoryRelationshipDefinitionRepository):
    def __init__(self) -> None:
        super().__init__()
        self.list_calls = 0
        self.add_calls = 0
        self.delete_calls = 0

    def list(self) -> tuple[RelationshipDefinition, ...]:
        self.list_calls += 1
        return super().list()

    def add(self, definition: RelationshipDefinition) -> None:
        self.add_calls += 1
        super().add(definition)

    def delete(self, definition_id: UUID) -> None:
        self.delete_calls += 1
        super().delete(definition_id)


class FakeUnitOfWork(ObjectTemplateUnitOfWork):
    def __init__(
        self,
        datatypes: InMemoryDataTypeRepository,
        object_templates: TrackingObjectTemplateRepository,
        objects: InMemoryObjectRepository,
        relationship_definitions: TrackingRelationshipDefinitionRepository,
        commits: list[int],
    ) -> None:
        self._datatypes = datatypes
        self._object_templates = object_templates
        self._objects = objects
        self._relationship_definitions = relationship_definitions
        self._commits = commits

    @property
    def datatypes(self) -> InMemoryDataTypeRepository:
        return self._datatypes

    @property
    def object_templates(self) -> TrackingObjectTemplateRepository:
        return self._object_templates

    @property
    def objects(self) -> InMemoryObjectRepository:
        return self._objects

    @property
    def relationship_definitions(self) -> TrackingRelationshipDefinitionRepository:
        return self._relationship_definitions

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self._commits[0] += 1


def _service() -> tuple[
    ObjectTemplateApplicationService,
    TrackingObjectTemplateRepository,
    TrackingRelationshipDefinitionRepository,
    list[int],
]:
    datatypes = InMemoryDataTypeRepository()
    object_templates = TrackingObjectTemplateRepository()
    objects = InMemoryObjectRepository()
    relationship_definitions = TrackingRelationshipDefinitionRepository()
    commits = [0]

    def factory() -> FakeUnitOfWork:
        return FakeUnitOfWork(
            datatypes,
            object_templates,
            objects,
            relationship_definitions,
            commits,
        )

    return (
        ObjectTemplateApplicationService(
            factory,
            model_write_uow_factory=factory,
        ),
        object_templates,
        relationship_definitions,
        commits,
    )


def _template(name: str) -> ObjectTemplate:
    return ObjectTemplate(
        id=uuid4(),
        namespace="network",
        name=name,
        description=f"{name} template",
        abstract=False,
    )


def _version(
    template_id: UUID,
    version: int,
    *,
    status: ObjectTemplateVersionStatus,
    parent: ObjectTemplateVersionRef | None = None,
) -> ObjectTemplateVersion:
    return ObjectTemplateVersion(
        template_id=template_id,
        version=version,
        status=status,
        parent=parent,
    )


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


def _reset_tracking_state(
    object_templates: TrackingObjectTemplateRepository,
    relationship_definitions: TrackingRelationshipDefinitionRepository,
) -> None:
    object_templates.replace_version_calls.clear()
    relationship_definitions.list_calls = 0
    relationship_definitions.add_calls = 0
    relationship_definitions.delete_calls = 0


def test_publish_with_no_relationship_definitions_succeeds() -> None:
    service, object_templates, relationship_definitions, commits = _service()
    template = _template("router")
    draft = _version(template.id, 1, status=ObjectTemplateVersionStatus.DRAFT)
    _store_template_versions(object_templates, template, (draft,))
    _reset_tracking_state(object_templates, relationship_definitions)

    published = service.publish_version(template_id=template.id, version=1)

    assert published.status is ObjectTemplateVersionStatus.PUBLISHED
    assert relationship_definitions.list_calls == 1
    assert object_templates.replace_version_calls == [published]
    assert commits[0] == 1


def test_unrelated_relationship_definitions_do_not_block_publish() -> None:
    service, object_templates, relationship_definitions, commits = _service()
    router = _template("router")
    router_draft = _version(router.id, 1, status=ObjectTemplateVersionStatus.DRAFT)
    source = _template("source")
    target = _template("target")
    _store_template_versions(object_templates, router, (router_draft,))
    _store_template_versions(
        object_templates,
        source,
        (_version(source.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED),),
    )
    _store_template_versions(
        object_templates,
        target,
        (_version(target.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED),),
    )
    relationship_definitions.add(
        _definition(source_template_id=source.id, target_template_id=target.id)
    )
    _reset_tracking_state(object_templates, relationship_definitions)

    published = service.publish_version(template_id=router.id, version=1)

    assert published.status is ObjectTemplateVersionStatus.PUBLISHED
    assert object_templates.replace_version_calls == [published]
    assert commits[0] == 1


def test_publish_rejects_source_side_prospective_conflict_before_replace() -> None:
    service, object_templates, relationship_definitions, commits = _service()
    network_device = _template("network_device")
    router = _template("router")
    credential = _template("credential")
    nd_v1 = _version(network_device.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    router_v1 = _version(
        router.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
    )
    router_v2 = _version(
        router.id,
        2,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
    )
    cred_v1 = _version(credential.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    _store_template_versions(object_templates, network_device, (nd_v1,))
    _store_template_versions(object_templates, router, (router_v1, router_v2))
    _store_template_versions(object_templates, credential, (cred_v1,))
    relationship_definitions.add(
        _definition(source_template_id=network_device.id, target_template_id=credential.id)
    )
    relationship_definitions.add(
        _definition(source_template_id=router.id, target_template_id=credential.id)
    )
    _reset_tracking_state(object_templates, relationship_definitions)

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.publish_version(template_id=router.id, version=2)

    assert object_templates.get_version(router.id, 2) == router_v2
    assert object_templates.replace_version_calls == []
    assert relationship_definitions.add_calls == 0
    assert relationship_definitions.delete_calls == 0
    assert commits[0] == 0


def test_publish_rejects_target_side_prospective_conflict() -> None:
    service, object_templates, relationship_definitions, commits = _service()
    network_device = _template("network_device")
    credential = _template("credential")
    tacacs = _template("tacacs_credential")
    nd_v1 = _version(network_device.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    cred_v1 = _version(credential.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    tacacs_v1 = _version(
        tacacs.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=ObjectTemplateVersionRef(template_id=credential.id, version=1),
    )
    tacacs_v2 = _version(
        tacacs.id,
        2,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=credential.id, version=1),
    )
    _store_template_versions(object_templates, network_device, (nd_v1,))
    _store_template_versions(object_templates, credential, (cred_v1,))
    _store_template_versions(object_templates, tacacs, (tacacs_v1, tacacs_v2))
    relationship_definitions.add(
        _definition(source_template_id=network_device.id, target_template_id=credential.id)
    )
    relationship_definitions.add(
        _definition(source_template_id=network_device.id, target_template_id=tacacs.id)
    )
    _reset_tracking_state(object_templates, relationship_definitions)

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.publish_version(template_id=tacacs.id, version=2)

    assert object_templates.get_version(tacacs.id, 2) == tacacs_v2
    assert object_templates.replace_version_calls == []
    assert commits[0] == 0


def test_publish_rejects_inverse_orientation_conflict() -> None:
    service, object_templates, relationship_definitions, commits = _service()
    network_device = _template("network_device")
    router = _template("router")
    credential = _template("credential")
    nd_v1 = _version(network_device.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    router_v1 = _version(
        router.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
    )
    router_v2 = _version(
        router.id,
        2,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
    )
    cred_v1 = _version(credential.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    _store_template_versions(object_templates, network_device, (nd_v1,))
    _store_template_versions(object_templates, router, (router_v1, router_v2))
    _store_template_versions(object_templates, credential, (cred_v1,))
    relationship_definitions.add(
        _definition(source_template_id=network_device.id, target_template_id=credential.id)
    )
    relationship_definitions.add(
        _definition(
            source_template_id=credential.id,
            target_template_id=router.id,
            forward_name="is_used_by",
            reverse_name="uses",
        )
    )
    _reset_tracking_state(object_templates, relationship_definitions)

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.publish_version(template_id=router.id, version=2)

    assert object_templates.replace_version_calls == []
    assert commits[0] == 0


def test_publish_rejects_symmetric_name_conflict() -> None:
    service, object_templates, relationship_definitions, commits = _service()
    network_device = _template("network_device")
    router = _template("router")
    credential = _template("credential")
    nd_v1 = _version(network_device.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    router_v1 = _version(
        router.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
    )
    router_v2 = _version(
        router.id,
        2,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
    )
    cred_v1 = _version(credential.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    _store_template_versions(object_templates, network_device, (nd_v1,))
    _store_template_versions(object_templates, router, (router_v1, router_v2))
    _store_template_versions(object_templates, credential, (cred_v1,))
    relationship_definitions.add(
        _definition(
            source_template_id=network_device.id,
            target_template_id=credential.id,
            forward_name="connects_to",
            reverse_name="connects_to",
        )
    )
    _reset_tracking_state(object_templates, relationship_definitions)
    relationship_definitions.add(
        _definition(
            source_template_id=credential.id,
            target_template_id=router.id,
            forward_name="connects_to",
            reverse_name="connects_to",
        )
    )
    _reset_tracking_state(object_templates, relationship_definitions)

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.publish_version(template_id=router.id, version=2)

    assert object_templates.replace_version_calls == []
    assert commits[0] == 0


def test_publish_allows_different_semantics_even_when_endpoint_spaces_overlap() -> None:
    service, object_templates, relationship_definitions, commits = _service()
    network_device = _template("network_device")
    router = _template("router")
    credential = _template("credential")
    nd_v1 = _version(network_device.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    router_v1 = _version(
        router.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
    )
    router_v2 = _version(
        router.id,
        2,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
    )
    cred_v1 = _version(credential.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    _store_template_versions(object_templates, network_device, (nd_v1,))
    _store_template_versions(object_templates, router, (router_v1, router_v2))
    _store_template_versions(object_templates, credential, (cred_v1,))
    relationship_definitions.add(
        _definition(source_template_id=network_device.id, target_template_id=credential.id)
    )
    relationship_definitions.add(
        _definition(
            source_template_id=router.id,
            target_template_id=credential.id,
            forward_name="manages",
            reverse_name="managed_by",
        )
    )
    _reset_tracking_state(object_templates, relationship_definitions)

    published = service.publish_version(template_id=router.id, version=2)

    assert published.status is ObjectTemplateVersionStatus.PUBLISHED
    assert object_templates.replace_version_calls == [published]
    assert commits[0] == 1


def test_unrelated_draft_versions_remain_excluded_from_conflict_analysis() -> None:
    service, object_templates, relationship_definitions, commits = _service()
    template = _template("router")
    draft = _version(template.id, 1, status=ObjectTemplateVersionStatus.DRAFT)
    network_device = _template("network_device")
    credential = _template("credential")
    draft_child = _template("draft_child")
    nd_v1 = _version(network_device.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    cred_v1 = _version(credential.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    draft_child_v1 = _version(
        draft_child.id,
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
    )
    _store_template_versions(object_templates, template, (draft,))
    _store_template_versions(object_templates, network_device, (nd_v1,))
    _store_template_versions(object_templates, credential, (cred_v1,))
    _store_template_versions(object_templates, draft_child, (draft_child_v1,))
    relationship_definitions.add(
        _definition(source_template_id=network_device.id, target_template_id=credential.id)
    )
    relationship_definitions.add(
        _definition(source_template_id=draft_child.id, target_template_id=credential.id)
    )

    published = service.publish_version(template_id=template.id, version=1)

    assert published.status is ObjectTemplateVersionStatus.PUBLISHED
    assert commits[0] == 1


@pytest.mark.parametrize(
    "historical_status",
    [
        ObjectTemplateVersionStatus.PUBLISHED,
        ObjectTemplateVersionStatus.DEPRECATED,
    ],
)
def test_historical_published_and_deprecated_versions_remain_relevant(
    historical_status: ObjectTemplateVersionStatus,
) -> None:
    service, object_templates, relationship_definitions, commits = _service()
    network_device = _template("network_device")
    router = _template("router")
    credential = _template("credential")
    network_v1 = _version(network_device.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    router_v1 = _version(
        router.id,
        1,
        status=historical_status,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
    )
    router_v2 = _version(
        router.id,
        2,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
    )
    credential_v1 = _version(credential.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    _store_template_versions(object_templates, network_device, (network_v1,))
    _store_template_versions(object_templates, router, (router_v1, router_v2))
    _store_template_versions(object_templates, credential, (credential_v1,))
    relationship_definitions.add(
        _definition(source_template_id=network_device.id, target_template_id=credential.id)
    )
    relationship_definitions.add(
        _definition(source_template_id=router.id, target_template_id=credential.id)
    )
    _reset_tracking_state(object_templates, relationship_definitions)

    with pytest.raises(RelationshipDefinitionSemanticConflict):
        service.publish_version(template_id=router.id, version=2)

    assert object_templates.replace_version_calls == []
    assert commits[0] == 0


def test_publish_uses_actual_exact_ancestry_of_the_version_being_published() -> None:
    service, object_templates, relationship_definitions, commits = _service()
    network_device = _template("network_device")
    router = _template("router")
    credential = _template("credential")
    nd_v1 = _version(network_device.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    nd_v2 = _version(network_device.id, 2, status=ObjectTemplateVersionStatus.PUBLISHED)
    router_v1 = _version(
        router.id,
        1,
        status=ObjectTemplateVersionStatus.DEPRECATED,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=1),
    )
    router_v2 = _version(
        router.id,
        2,
        status=ObjectTemplateVersionStatus.DRAFT,
        parent=ObjectTemplateVersionRef(template_id=network_device.id, version=2),
    )
    cred_v1 = _version(credential.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    _store_template_versions(object_templates, network_device, (nd_v1, nd_v2))
    _store_template_versions(object_templates, router, (router_v1, router_v2))
    _store_template_versions(object_templates, credential, (cred_v1,))
    relationship_definitions.add(
        _definition(
            source_template_id=network_device.id,
            target_template_id=credential.id,
            forward_name="manages",
            reverse_name="managed_by",
        )
    )
    relationship_definitions.add(
        _definition(source_template_id=router.id, target_template_id=credential.id)
    )
    _reset_tracking_state(object_templates, relationship_definitions)

    published = service.publish_version(template_id=router.id, version=2)

    assert published.status is ObjectTemplateVersionStatus.PUBLISHED
    assert published.parent == ObjectTemplateVersionRef(
        template_id=network_device.id,
        version=2,
    )
    assert object_templates.replace_version_calls == [published]
    assert commits[0] == 1


def test_publish_conflict_engine_propagates_missing_parent_from_historical_ancestry() -> None:
    service, object_templates, relationship_definitions, commits = _service()
    network_device = _template("network_device")
    router = _template("router")
    credential = _template("credential")
    published_template = _template("published_template")
    _store_template_versions(
        object_templates,
        network_device,
        (_version(network_device.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED),),
    )
    _store_template_versions(
        object_templates,
        router,
        (
            _version(
                router.id,
                1,
                status=ObjectTemplateVersionStatus.DEPRECATED,
                parent=ObjectTemplateVersionRef(template_id=uuid4(), version=1),
            ),
        ),
    )
    _store_template_versions(
        object_templates,
        credential,
        (_version(credential.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED),),
    )
    _store_template_versions(
        object_templates,
        published_template,
        (_version(published_template.id, 1, status=ObjectTemplateVersionStatus.DRAFT),),
    )
    relationship_definitions.add(
        _definition(source_template_id=network_device.id, target_template_id=credential.id)
    )
    relationship_definitions.add(
        _definition(source_template_id=router.id, target_template_id=credential.id)
    )
    _reset_tracking_state(object_templates, relationship_definitions)

    with pytest.raises(ObjectTemplateParentNotFound):
        service.publish_version(template_id=published_template.id, version=1)

    assert object_templates.replace_version_calls == []
    assert commits[0] == 0


def test_publish_conflict_engine_propagates_self_inheritance_from_historical_ancestry() -> None:
    service, object_templates, relationship_definitions, commits = _service()
    network_device = _template("network_device")
    router = _template("router")
    credential = _template("credential")
    published_template = _template("published_template")
    _store_template_versions(
        object_templates,
        network_device,
        (_version(network_device.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED),),
    )
    _store_template_versions(
        object_templates,
        router,
        (
            _version(
                router.id,
                1,
                status=ObjectTemplateVersionStatus.DEPRECATED,
                parent=ObjectTemplateVersionRef(template_id=router.id, version=1),
            ),
        ),
    )
    _store_template_versions(
        object_templates,
        credential,
        (_version(credential.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED),),
    )
    _store_template_versions(
        object_templates,
        published_template,
        (_version(published_template.id, 1, status=ObjectTemplateVersionStatus.DRAFT),),
    )
    relationship_definitions.add(
        _definition(source_template_id=network_device.id, target_template_id=credential.id)
    )
    relationship_definitions.add(
        _definition(source_template_id=router.id, target_template_id=credential.id)
    )
    _reset_tracking_state(object_templates, relationship_definitions)

    with pytest.raises(ObjectTemplateSelfInheritance):
        service.publish_version(template_id=published_template.id, version=1)

    assert object_templates.replace_version_calls == []
    assert commits[0] == 0


def test_publish_conflict_engine_propagates_inheritance_cycle_from_historical_ancestry() -> None:
    service, object_templates, relationship_definitions, commits = _service()
    network_device = _template("network_device")
    router = _template("router")
    cycle_partner = _template("cycle_partner")
    credential = _template("credential")
    published_template = _template("published_template")
    _store_template_versions(
        object_templates,
        network_device,
        (_version(network_device.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED),),
    )
    _store_template_versions(
        object_templates,
        router,
        (
            _version(
                router.id,
                1,
                status=ObjectTemplateVersionStatus.DEPRECATED,
                parent=ObjectTemplateVersionRef(template_id=cycle_partner.id, version=1),
            ),
        ),
    )
    _store_template_versions(
        object_templates,
        cycle_partner,
        (
            _version(
                cycle_partner.id,
                1,
                status=ObjectTemplateVersionStatus.PUBLISHED,
                parent=ObjectTemplateVersionRef(template_id=router.id, version=1),
            ),
        ),
    )
    _store_template_versions(
        object_templates,
        credential,
        (_version(credential.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED),),
    )
    _store_template_versions(
        object_templates,
        published_template,
        (_version(published_template.id, 1, status=ObjectTemplateVersionStatus.DRAFT),),
    )
    relationship_definitions.add(
        _definition(source_template_id=network_device.id, target_template_id=credential.id)
    )
    relationship_definitions.add(
        _definition(source_template_id=router.id, target_template_id=credential.id)
    )
    _reset_tracking_state(object_templates, relationship_definitions)

    with pytest.raises(ObjectTemplateInheritanceCycle):
        service.publish_version(template_id=published_template.id, version=1)

    assert object_templates.replace_version_calls == []
    assert commits[0] == 0

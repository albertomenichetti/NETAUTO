import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from netauto.core.objecttemplate import (
    ObjectTemplate,
    ObjectTemplateAlreadyExists,
    ObjectTemplateComponent,
    ObjectTemplateNotFound,
    ObjectTemplatePersistenceError,
    ObjectTemplateProperty,
    ObjectTemplateVersion,
    ObjectTemplateVersionAlreadyExists,
    ObjectTemplateVersionNotFound,
    ObjectTemplateVersionRef,
    ObjectTemplateVersionStatus,
)
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.models import (
    ObjectTemplateRow,
    ObjectTemplateVersionRow,
    RelationshipDefinitionRow,
)
from netauto.persistence.sqlalchemy.objecttemplate_repository import (
    SqlAlchemyObjectTemplateRepository,
)


def _template(
    *,
    namespace: str = "network",
    name: str = "device",
    description: str | None = "Network device template",
    abstract: bool = False,
    template_id: UUID | None = None,
) -> ObjectTemplate:
    return ObjectTemplate(
        id=template_id or uuid4(),
        namespace=namespace,
        name=name,
        description=description,
        abstract=abstract,
    )


def _property(
    name: str,
    *,
    datatype_id: UUID | None = None,
    datatype_version: int = 1,
    required: bool = False,
) -> ObjectTemplateProperty:
    return ObjectTemplateProperty(
        name=name,
        datatype_id=datatype_id or uuid4(),
        datatype_version=datatype_version,
        required=required,
    )


def _component(
    name: str,
    *,
    template_id: UUID | None = None,
    template_version: int = 1,
) -> ObjectTemplateComponent:
    del template_version
    return ObjectTemplateComponent(
        name=name,
        template_id=template_id or uuid4(),
    )


def _version(
    template_id: UUID,
    version: int,
    *,
    status: ObjectTemplateVersionStatus = ObjectTemplateVersionStatus.DRAFT,
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


def _repo(
    tmp_path: Path,
    filename: str,
) -> tuple[SqlAlchemyObjectTemplateRepository, Session, Engine]:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / filename}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    return SqlAlchemyObjectTemplateRepository(session), session, engine


def test_empty_list(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "empty.sqlite3")
    try:
        assert repo.list() == ()
    finally:
        session.close()
        engine.dispose()


def test_add_get_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "round_trip.sqlite3")
    template = _template()
    try:
        repo.add(template)
        assert repo.get(template.id) == template
    finally:
        session.close()
        engine.dispose()


@pytest.mark.parametrize(
    ("description", "abstract", "name"),
    [(None, False, "device_plain"), ("desc", True, "device_abstract")],
)
def test_description_and_abstract_round_trip(
    tmp_path: Path,
    description: str | None,
    abstract: bool,
    name: str,
) -> None:
    repo, session, engine = _repo(tmp_path, f"identity_{abstract}.sqlite3")
    template = _template(
        name=name,
        description=description,
        abstract=abstract,
    )
    try:
        repo.add(template)
        loaded = repo.get(template.id)
        assert loaded is not None
        assert loaded.description == description
        assert loaded.abstract is abstract
    finally:
        session.close()
        engine.dispose()


def test_get_by_name(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "by_name.sqlite3")
    template = _template(namespace="network", name="router")
    try:
        repo.add(template)
        assert repo.get_by_name("network", "router") == template
    finally:
        session.close()
        engine.dispose()


def test_deterministic_ordering(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "ordering.sqlite3")
    zeta = _template(namespace="zeta", name="beta", description=None)
    device = _template(namespace="network", name="device", description=None)
    router = _template(namespace="network", name="router", description=None)
    try:
        repo.add(zeta)
        repo.add(router)
        repo.add(device)
        listed = repo.list()
        assert [(template.namespace, template.name) for template in listed] == [
            ("network", "device"),
            ("network", "router"),
            ("zeta", "beta"),
        ]
    finally:
        session.close()
        engine.dispose()


def test_duplicate_uuid_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "dup_uuid.sqlite3")
    template = _template(template_id=uuid4(), namespace="network", name="device")
    duplicate = _template(template_id=template.id, namespace="network", name="router")
    try:
        repo.add(template)
        with pytest.raises(ObjectTemplateAlreadyExists):
            repo.add(duplicate)
    finally:
        session.close()
        engine.dispose()


def test_duplicate_logical_name_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "dup_name.sqlite3")
    first = _template(namespace="network", name="device")
    second = _template(namespace="network", name="device")
    try:
        repo.add(first)
        with pytest.raises(ObjectTemplateAlreadyExists):
            repo.add(second)
    finally:
        session.close()
        engine.dispose()


def test_add_get_version_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "version_round_trip.sqlite3")
    template = _template()
    version = _version(
        template.id,
        1,
        properties=(
            _property("hostname", required=True),
            _property("serial"),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(version)
        assert repo.get_version(template.id, 1) == version
    finally:
        session.close()
        engine.dispose()


def test_status_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "status.sqlite3")
    template = _template()
    draft = _version(template.id, 1, status=ObjectTemplateVersionStatus.DRAFT)
    published = _version(template.id, 2, status=ObjectTemplateVersionStatus.PUBLISHED)
    deprecated = _version(template.id, 3, status=ObjectTemplateVersionStatus.DEPRECATED)
    try:
        repo.add(template)
        repo.add_version(draft)
        repo.add_version(published)
        repo.add_version(deprecated)
        loaded = repo.list_versions(template.id)
        assert tuple(version.status for version in loaded) == (
            ObjectTemplateVersionStatus.DRAFT,
            ObjectTemplateVersionStatus.PUBLISHED,
            ObjectTemplateVersionStatus.DEPRECATED,
        )
    finally:
        session.close()
        engine.dispose()


def test_parent_none_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "parent_none.sqlite3")
    template = _template()
    version = _version(template.id, 1)
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded is not None
        assert loaded.parent is None
    finally:
        session.close()
        engine.dispose()


def test_exact_pinned_parent_ref_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "parent.sqlite3")
    template = _template()
    version = _version(
        template.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=uuid4(), version=7),
    )
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded is not None
        assert loaded.parent == version.parent
    finally:
        session.close()
        engine.dispose()


def test_multiple_ordered_properties_round_trip_and_order_preserved(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "properties.sqlite3")
    template = _template()
    first_datatype_id = uuid4()
    second_datatype_id = uuid4()
    version = _version(
        template.id,
        1,
        properties=(
            _property(
                "hostname",
                datatype_id=first_datatype_id,
                datatype_version=2,
                required=True,
            ),
            _property(
                "serial",
                datatype_id=second_datatype_id,
                datatype_version=3,
                required=False,
            ),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded is not None
        assert tuple(prop.name for prop in loaded.properties) == ("hostname", "serial")
        assert loaded.properties[0].required is True
        assert loaded.properties[1].required is False
        assert loaded.properties[0].datatype_id == first_datatype_id
        assert loaded.properties[0].datatype_version == 2
        assert loaded.properties[1].datatype_id == second_datatype_id
        assert loaded.properties[1].datatype_version == 3
    finally:
        session.close()
        engine.dispose()


def test_empty_components_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "empty_components.sqlite3")
    template = _template()
    version = _version(template.id, 1)
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded is not None
        assert loaded.components == ()
    finally:
        session.close()
        engine.dispose()


def test_one_component_round_trip(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "one_component.sqlite3")
    template = _template()
    component = _component("interfaces", template_id=uuid4(), template_version=7)
    version = _version(template.id, 1, components=(component,))
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded is not None
        assert loaded.components == (component,)
    finally:
        session.close()
        engine.dispose()


def test_multiple_ordered_components_round_trip_and_order_preserved(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "components.sqlite3")
    template = _template()
    first_target = uuid4()
    second_target = uuid4()
    version = _version(
        template.id,
        1,
        components=(
            _component("interfaces", template_id=first_target, template_version=2),
            _component("modules", template_id=second_target, template_version=5),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded is not None
        assert tuple(component.name for component in loaded.components) == (
            "interfaces",
            "modules",
        )
        assert loaded.components[0].template_id == first_target
        assert loaded.components[1].template_id == second_target
    finally:
        session.close()
        engine.dispose()


def test_delete_removes_identity_and_owned_versions_only(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "delete.sqlite3")
    target = _template(name="device")
    unrelated = _template(name="router")
    try:
        repo.add(target)
        repo.add(unrelated)
        repo.add_version(_version(target.id, 1))
        repo.add_version(_version(target.id, 2, status=ObjectTemplateVersionStatus.PUBLISHED))
        repo.add_version(_version(unrelated.id, 1))

        repo.delete(target.id)

        assert repo.get(target.id) is None
        assert repo.list_versions(target.id) == ()
        assert repo.get(unrelated.id) == unrelated
        assert tuple(version.version for version in repo.list_versions(unrelated.id)) == (1,)
    finally:
        session.close()
        engine.dispose()


def test_delete_missing_identity_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "delete_missing.sqlite3")
    try:
        with pytest.raises(ObjectTemplateNotFound):
            repo.delete(uuid4())
    finally:
        session.close()
        engine.dispose()


def test_delete_does_not_commit_inside_repository(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "delete_no_commit.sqlite3")
    target = _template(name="device")
    try:
        repo.add(target)
        repo.add_version(_version(target.id, 1))
        session.commit()

        repo.delete(target.id)

        assert session.in_transaction()
        session.rollback()
        assert repo.get(target.id) == target
    finally:
        session.close()
        engine.dispose()


def test_delete_relationship_definition_fk_restrict_maps_to_persistence_error(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "delete_fk_restrict.sqlite3")
    source = _template(name="device")
    target = _template(name="credential")
    try:
        repo.add(source)
        repo.add(target)
        repo.add_version(_version(source.id, 1))
        repo.add_version(_version(target.id, 1))
        session.add(
            RelationshipDefinitionRow(
                id=str(uuid4()),
                source_template_id=str(source.id),
                target_template_id=str(target.id),
                forward_name="uses",
                reverse_name="is_used_by",
            )
        )
        session.flush()

        with pytest.raises(ObjectTemplatePersistenceError):
            repo.delete(source.id)
    finally:
        session.close()
        engine.dispose()


def test_properties_and_components_coexist_in_same_version(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "properties_components.sqlite3")
    template = _template()
    version = _version(
        template.id,
        1,
        properties=(_property("hostname", required=True),),
        components=(_component("interfaces", template_id=uuid4(), template_version=3),),
    )
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded == version
    finally:
        session.close()
        engine.dispose()


def test_missing_owning_template_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "missing_owner.sqlite3")
    version = _version(uuid4(), 1)
    try:
        with pytest.raises(ObjectTemplateNotFound, match="Owning object template does not exist."):
            repo.add_version(version)
    finally:
        session.close()
        engine.dispose()


def test_duplicate_version_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "dup_version.sqlite3")
    template = _template()
    version = _version(template.id, 1)
    try:
        repo.add(template)
        repo.add_version(version)
        with pytest.raises(ObjectTemplateVersionAlreadyExists):
            repo.add_version(version)
    finally:
        session.close()
        engine.dispose()


def test_list_versions_ascending(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "list_versions.sqlite3")
    template = _template()
    v5 = _version(template.id, 5, status=ObjectTemplateVersionStatus.DEPRECATED)
    v1 = _version(template.id, 1, status=ObjectTemplateVersionStatus.PUBLISHED)
    v2 = _version(template.id, 2)
    try:
        repo.add(template)
        repo.add_version(v5)
        repo.add_version(v1)
        repo.add_version(v2)
        versions = repo.list_versions(template.id)
        assert tuple(version.version for version in versions) == (1, 2, 5)
    finally:
        session.close()
        engine.dispose()


def test_replace_version_with_revised_properties(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_props.sqlite3")
    template = _template()
    original = _version(template.id, 1, properties=(_property("hostname"),))
    replacement = _version(template.id, 1, properties=(_property("serial"),))
    try:
        repo.add(template)
        repo.add_version(original)
        repo.replace_version(replacement)
        loaded = repo.get_version(template.id, 1)
        assert loaded == replacement
    finally:
        session.close()
        engine.dispose()


def test_replace_version_replaces_components(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_components.sqlite3")
    template = _template()
    original = _version(
        template.id,
        1,
        components=(_component("interfaces", template_id=uuid4(), template_version=1),),
    )
    replacement = _version(
        template.id,
        1,
        components=(_component("modules", template_id=uuid4(), template_version=7),),
    )
    try:
        repo.add(template)
        repo.add_version(original)
        repo.replace_version(replacement)
        loaded = repo.get_version(template.id, 1)
        assert loaded == replacement
    finally:
        session.close()
        engine.dispose()


def test_replace_version_with_changed_parent(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_parent.sqlite3")
    template = _template()
    original = _version(template.id, 1, parent=None)
    replacement = _version(
        template.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=uuid4(), version=2),
    )
    try:
        repo.add(template)
        repo.add_version(original)
        repo.replace_version(replacement)
        loaded = repo.get_version(template.id, 1)
        assert loaded == replacement
    finally:
        session.close()
        engine.dispose()


def test_replace_lifecycle_snapshot_preserves_complete_replacement_snapshot(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_status.sqlite3")
    template = _template()
    original = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.DRAFT,
        properties=(_property("hostname"),),
        components=(_component("interfaces", template_id=uuid4(), template_version=2),),
    )
    replacement = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        properties=(_property("serial"),),
        components=(_component("modules", template_id=uuid4(), template_version=9),),
    )
    try:
        repo.add(template)
        repo.add_version(original)
        repo.replace_version(replacement)
        loaded = repo.get_version(template.id, 1)
        assert loaded == replacement
        assert loaded is not None
        assert loaded.status is ObjectTemplateVersionStatus.PUBLISHED
        assert tuple(prop.name for prop in loaded.properties) == ("serial",)
        assert tuple(component.name for component in loaded.components) == ("modules",)
    finally:
        session.close()
        engine.dispose()


def test_replace_missing_rejected(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_missing.sqlite3")
    template = _template()
    version = _version(template.id, 1)
    try:
        repo.add(template)
        with pytest.raises(ObjectTemplateVersionNotFound):
            repo.replace_version(version)
    finally:
        session.close()
        engine.dispose()


def test_malformed_stored_uuid_produces_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "bad_uuid.sqlite3")
    try:
        session.add(
            ObjectTemplateRow(
                id="not-a-uuid",
                namespace="network",
                name="device",
                description=None,
                abstract=False,
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_by_name("network", "device")
    finally:
        session.close()
        engine.dispose()


def test_malformed_status_produces_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "bad_status.sqlite3")
    template = _template()
    try:
        repo.add(template)
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status="invalid",
                parent_template_id=None,
                parent_version=None,
                properties_json="[]",
                components_json="[]",
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_version(template.id, 1)
    finally:
        session.close()
        engine.dispose()


def test_malformed_properties_json_produces_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "bad_json.sqlite3")
    template = _template()
    try:
        repo.add(template)
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
                properties_json="{bad json",
                components_json="[]",
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_version(template.id, 1)
    finally:
        session.close()
        engine.dispose()


def test_malformed_components_json_produces_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "bad_components_json.sqlite3")
    template = _template()
    try:
        repo.add(template)
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
                properties_json="[]",
                components_json="{bad json",
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_version(template.id, 1)
    finally:
        session.close()
        engine.dispose()


def test_malformed_property_shape_produces_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "bad_property_shape.sqlite3")
    template = _template()
    payload = [{"name": "hostname", "datatype_id": str(uuid4())}]
    try:
        repo.add(template)
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
                properties_json=json.dumps(payload, sort_keys=True, separators=(",", ":")),
                components_json="[]",
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_version(template.id, 1)
    finally:
        session.close()
        engine.dispose()


def test_components_json_top_level_non_array_produces_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "components_not_array.sqlite3")
    template = _template()
    try:
        repo.add(template)
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
                properties_json="[]",
                components_json='{"name":"interfaces"}',
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_version(template.id, 1)
    finally:
        session.close()
        engine.dispose()


def test_component_entry_non_object_produces_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "component_not_object.sqlite3")
    template = _template()
    try:
        repo.add(template)
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
                properties_json="[]",
                components_json='["interfaces"]',
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_version(template.id, 1)
    finally:
        session.close()
        engine.dispose()


@pytest.mark.parametrize(
    "payload",
    [
        [
            {
                "name": "interfaces",
                "template_id": str(uuid4()),
                "template_version": 1,
                "extra": True,
            }
        ],
    ],
)
def test_component_shape_errors_produce_persistence_error(
    tmp_path: Path,
    payload: list[object],
) -> None:
    repo, session, engine = _repo(tmp_path, "component_shape.sqlite3")
    template = _template()
    try:
        repo.add(template)
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
                properties_json="[]",
                components_json=json.dumps(payload, sort_keys=True, separators=(",", ":")),
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_version(template.id, 1)
    finally:
        session.close()
        engine.dispose()


def test_component_malformed_uuid_produces_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "component_bad_uuid.sqlite3")
    template = _template()
    payload = [{"name": "interfaces", "template_id": "not-a-uuid"}]
    try:
        repo.add(template)
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
                properties_json="[]",
                components_json=json.dumps(payload, sort_keys=True, separators=(",", ":")),
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_version(template.id, 1)
    finally:
        session.close()
        engine.dispose()


def test_legacy_component_entry_with_template_version_is_accepted_and_ignored(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "component_legacy_version.sqlite3")
    template = _template()
    target_id = uuid4()
    payload = [{"name": "interfaces", "template_id": str(target_id), "template_version": 7}]
    try:
        repo.add(template)
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=None,
                parent_version=None,
                properties_json="[]",
                components_json=json.dumps(payload, sort_keys=True, separators=(",", ":")),
            )
        )
        session.flush()
        loaded = repo.get_version(template.id, 1)
        assert loaded is not None
        assert loaded.components == (
            ObjectTemplateComponent(
                name="interfaces",
                template_id=target_id,
            ),
        )
    finally:
        session.close()
        engine.dispose()


def test_partial_parent_reference_produces_persistence_error(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "partial_parent.sqlite3")
    template = _template()
    try:
        repo.add(template)
        session.add(
            ObjectTemplateVersionRow(
                template_id=str(template.id),
                version=1,
                status=ObjectTemplateVersionStatus.DRAFT.value,
                parent_template_id=str(uuid4()),
                parent_version=None,
                properties_json="[]",
                components_json="[]",
            )
        )
        session.flush()
        with pytest.raises(ObjectTemplatePersistenceError):
            repo.get_version(template.id, 1)
    finally:
        session.close()
        engine.dispose()


def test_repository_does_not_require_parent_version_to_exist(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "no_parent_validation.sqlite3")
    template = _template()
    version = _version(
        template.id,
        1,
        parent=ObjectTemplateVersionRef(template_id=uuid4(), version=9),
    )
    try:
        repo.add(template)
        repo.add_version(version)
        assert repo.get_version(template.id, 1) == version
    finally:
        session.close()
        engine.dispose()


def test_repository_does_not_require_datatype_version_to_exist_or_be_published(
    tmp_path: Path,
) -> None:
    repo, session, engine = _repo(tmp_path, "no_datatype_validation.sqlite3")
    template = _template()
    version = _version(
        template.id,
        1,
        properties=(
            _property("hostname", datatype_id=uuid4(), datatype_version=3, required=True),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded == version
    finally:
        session.close()
        engine.dispose()


def test_add_version_does_not_require_component_target_to_exist(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "no_component_target_validation.sqlite3")
    template = _template()
    version = _version(
        template.id,
        1,
        components=(
            _component("interfaces", template_id=uuid4(), template_version=7),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(version)
        loaded = repo.get_version(template.id, 1)
        assert loaded == version
    finally:
        session.close()
        engine.dispose()


def test_replace_version_does_not_validate_component_target_semantics(tmp_path: Path) -> None:
    repo, session, engine = _repo(tmp_path, "replace_component_target.sqlite3")
    template = _template()
    original = _version(template.id, 1)
    replacement = _version(
        template.id,
        1,
        status=ObjectTemplateVersionStatus.PUBLISHED,
        components=(
            _component("interfaces", template_id=uuid4(), template_version=99),
        ),
    )
    try:
        repo.add(template)
        repo.add_version(original)
        repo.replace_version(replacement)
        loaded = repo.get_version(template.id, 1)
        assert loaded == replacement
    finally:
        session.close()
        engine.dispose()

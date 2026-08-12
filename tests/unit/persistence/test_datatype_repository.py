import importlib
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID

import pytest

from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataType,
    DataTypeAlreadyExists,
    DataTypeFactory,
    DataTypeNotFound,
    DataTypePersistenceError,
    DataTypeRepository,
    DataTypeVersion,
    DataTypeVersionAlreadyExists,
    DataTypeVersioningService,
    DataTypeVersionNotFound,
    DataTypeVersionStatus,
    PrimitiveTypeRegistry,
)
from netauto.persistence.memory.datatype_repository import InMemoryDataTypeRepository


@contextmanager
def _repository_harness(
    backend: str,
    tmp_path: Path,
) -> Iterator[DataTypeRepository]:
    del tmp_path
    if backend != "memory":
        raise AssertionError(f"Unknown backend '{backend}'.")
    yield InMemoryDataTypeRepository()


def _datatype(
    *,
    namespace: str = "network",
    name: str = "hostname",
    description: str | None = "Network hostname",
) -> DataType:
    return DataTypeFactory().create(
        namespace=namespace,
        name=name,
        description=description,
        base_type="core.string",
    )[0]


def _hostname_pair() -> tuple[DataType, DataTypeVersion]:
    return DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=1),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
        ),
    )


def _vlan_pair() -> tuple[DataType, DataTypeVersion]:
    return DataTypeFactory().create(
        namespace="network",
        name="vlan_id",
        description="VLAN identifier",
        base_type="core.integer",
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=1),
            Constraint(name=ConstraintName.MAXIMUM, value=4094),
        ),
    )


def _status_pair() -> tuple[DataType, DataTypeVersion]:
    return DataTypeFactory().create(
        namespace="asset",
        name="device_status",
        description="Device status",
        base_type="core.string",
        constraints=(
            Constraint(
                name=ConstraintName.ENUM,
                value=("active", "planned", "retired"),
            ),
        ),
    )


def _temporal_pair(
    *,
    namespace: str,
    name: str,
    description: str,
    base_type: str,
) -> tuple[DataType, DataTypeVersion]:
    return DataTypeFactory().create(
        namespace=namespace,
        name=name,
        description=description,
        base_type=base_type,
    )


@pytest.mark.parametrize("backend", ["memory"])
def test_repository_datatype_round_trip(backend: str, tmp_path: Path) -> None:
    datatype = _datatype()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)

        loaded = repo.get(datatype.id)

    assert loaded == datatype


@pytest.mark.parametrize("backend", ["memory"])
def test_uuid_remains_uuid_after_reload(backend: str, tmp_path: Path) -> None:
    datatype = _datatype()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        loaded = repo.get(datatype.id)

    assert loaded is not None
    assert isinstance(loaded.id, UUID)
    assert loaded.id == datatype.id


@pytest.mark.parametrize(
    ("description", "name"),
    [(None, "hostname"), ("Network hostname", "hostname_alt")],
)
@pytest.mark.parametrize("backend", ["memory"])
def test_description_round_trip(
    backend: str,
    tmp_path: Path,
    description: str | None,
    name: str,
) -> None:
    datatype = _datatype(name=name, description=description)

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        loaded = repo.get(datatype.id)

    assert loaded is not None
    assert loaded.description == description


@pytest.mark.parametrize("backend", ["memory"])
def test_get_by_name(backend: str, tmp_path: Path) -> None:
    datatype = _datatype()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        loaded = repo.get_by_name("network", "hostname")

    assert loaded == datatype


@pytest.mark.parametrize("backend", ["memory"])
def test_delete_removes_datatype_identity_and_all_versions(backend: str, tmp_path: Path) -> None:
    first, v1 = _hostname_pair()
    second, v2 = _vlan_pair()
    versioning = DataTypeVersioningService()
    v1_published = versioning.publish(v1)
    v1_next = versioning.create_next_version(v1_published, existing_versions=(v1_published,))

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(first)
        repo.add_version(v1)
        repo.add_version(v1_next)
        repo.add(second)
        repo.add_version(v2)

        repo.delete(first.id)

        assert repo.get(first.id) is None
        assert repo.get_by_name(first.namespace, first.name) is None
        assert repo.list_versions(first.id) == ()
        assert repo.get(second.id) == second
        assert repo.list_versions(second.id) == (v2,)


@pytest.mark.parametrize("backend", ["memory"])
def test_delete_missing_rejected(backend: str, tmp_path: Path) -> None:
    with _repository_harness(backend, tmp_path) as repo:
        with pytest.raises(DataTypeNotFound):
            repo.delete(UUID(int=1))


@pytest.mark.parametrize("backend", ["memory"])
def test_list_returns_deterministic_ordering(backend: str, tmp_path: Path) -> None:
    zeta = _datatype(namespace="zeta", name="beta", description=None)
    vlan = _datatype(namespace="network", name="vlan_id", description=None)
    hostname = _datatype(namespace="network", name="hostname", description=None)

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(zeta)
        repo.add(vlan)
        repo.add(hostname)
        listed = repo.list()

    assert [(datatype.namespace, datatype.name) for datatype in listed] == [
        ("network", "hostname"),
        ("network", "vlan_id"),
        ("zeta", "beta"),
    ]


@pytest.mark.parametrize("backend", ["memory"])
def test_duplicate_uuid_rejected(backend: str, tmp_path: Path) -> None:
    datatype = _datatype()
    duplicate = DataType(
        id=datatype.id,
        namespace="asset",
        name="status",
        description=None,
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        with pytest.raises(DataTypeAlreadyExists):
            repo.add(duplicate)


@pytest.mark.parametrize("backend", ["memory"])
def test_duplicate_logical_name_rejected(backend: str, tmp_path: Path) -> None:
    first = _datatype()
    second = _datatype()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(first)
        with pytest.raises(DataTypeAlreadyExists):
            repo.add(second)


@pytest.mark.parametrize("backend", ["memory"])
def test_version_add_and_get(backend: str, tmp_path: Path) -> None:
    datatype, version = _hostname_pair()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded == version


@pytest.mark.parametrize(
    ("base_type", "namespace", "name", "expected_format"),
    [
        ("core.date", "lifecycle", "warranty_expiration", "date"),
        ("core.datetime", "inventory", "last_seen", "date-time"),
        ("core.ip", "network", "ip_address", "ip"),
        ("core.ip_prefix", "network", "ip_prefix", "ip-prefix"),
    ],
)
@pytest.mark.parametrize("backend", ["memory"])
def test_formatted_string_datatype_version_round_trip_preserves_primitive_metadata(
    backend: str,
    tmp_path: Path,
    base_type: str,
    namespace: str,
    name: str,
    expected_format: str,
) -> None:
    datatype, version = _temporal_pair(
        namespace=namespace,
        name=name,
        description="Temporal datatype",
        base_type=base_type,
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded is not None
    assert loaded.base_type.name == base_type
    assert loaded.base_type.json_schema_type == "string"
    assert loaded.base_type.json_schema_format == expected_format


@pytest.mark.parametrize("backend", ["memory"])
def test_list_versions_ordered_ascending(backend: str, tmp_path: Path) -> None:
    datatype, v1_draft = _vlan_pair()
    service = DataTypeVersioningService()
    v1_published = service.publish(v1_draft)
    v2_draft = service.create_next_version(v1_published, existing_versions=(v1_published,))
    v5_draft = DataTypeVersion(
        datatype_id=datatype.id,
        version=5,
        status=DataTypeVersionStatus.DRAFT,
        base_type=v1_published.base_type,
        constraints=v1_published.constraints,
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(v1_draft)
        repo.replace_version(v1_published)
        repo.add_version(v5_draft)
        repo.add_version(v2_draft)

        versions = repo.list_versions(datatype.id)

    assert tuple(version.version for version in versions) == (1, 2, 5)


@pytest.mark.parametrize("backend", ["memory"])
def test_duplicate_version_rejected(backend: str, tmp_path: Path) -> None:
    datatype, version = _hostname_pair()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        with pytest.raises(DataTypeVersionAlreadyExists):
            repo.add_version(version)


@pytest.mark.parametrize("backend", ["memory"])
def test_missing_parent_rejected(backend: str, tmp_path: Path) -> None:
    _, version = _hostname_pair()

    with _repository_harness(backend, tmp_path) as repo:
        with pytest.raises(DataTypeNotFound):
            repo.add_version(version)


@pytest.mark.parametrize("backend", ["memory"])
def test_replace_version_existing(backend: str, tmp_path: Path) -> None:
    datatype, draft = _hostname_pair()
    service = DataTypeVersioningService()
    revised = service.revise_draft(
        draft,
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=5),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
        ),
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(draft)
        repo.replace_version(revised)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded == revised


@pytest.mark.parametrize("backend", ["memory"])
def test_add_version_requires_draft_status(backend: str, tmp_path: Path) -> None:
    datatype, draft = _hostname_pair()
    published = DataTypeVersioningService().publish(draft)
    deprecated = DataTypeVersioningService().deprecate(published)

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        with pytest.raises(DataTypePersistenceError):
            repo.add_version(published)
        with pytest.raises(DataTypePersistenceError):
            repo.add_version(deprecated)
        assert repo.get_version(datatype.id, 1) is None


@pytest.mark.parametrize("backend", ["memory"])
def test_add_version_preserves_duplicate_error_before_new_lifecycle_validation(
    backend: str,
    tmp_path: Path,
) -> None:
    datatype, draft = _hostname_pair()
    published = DataTypeVersioningService().publish(draft)

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(draft)
        with pytest.raises(DataTypeVersionAlreadyExists):
            repo.add_version(published)


@pytest.mark.parametrize("backend", ["memory"])
def test_add_version_rejects_cross_version_base_type_change(
    backend: str,
    tmp_path: Path,
) -> None:
    datatype, v1_draft = _hostname_pair()
    _, v2_integer = _vlan_pair()
    v2_draft = DataTypeVersion(
        datatype_id=datatype.id,
        version=2,
        status=DataTypeVersionStatus.DRAFT,
        base_type=v2_integer.base_type,
        constraints=v2_integer.constraints,
    )
    valid_v2 = DataTypeVersion(
        datatype_id=datatype.id,
        version=2,
        status=DataTypeVersionStatus.DRAFT,
        base_type=v1_draft.base_type,
        constraints=v1_draft.constraints,
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(v1_draft)
        with pytest.raises(DataTypePersistenceError):
            repo.add_version(v2_draft)
        assert repo.get_version(datatype.id, 2) is None
        repo.add_version(valid_v2)
        assert repo.get_version(datatype.id, 2) == valid_v2


@pytest.mark.parametrize("backend", ["memory"])
def test_replace_version_rejects_draft_base_type_change_without_mutating_storage(
    backend: str,
    tmp_path: Path,
) -> None:
    datatype, draft = _hostname_pair()
    integer_base = PrimitiveTypeRegistry().get("core.integer")
    illegal = DataTypeVersion(
        datatype_id=draft.datatype_id,
        version=draft.version,
        status=DataTypeVersionStatus.DRAFT,
        base_type=integer_base,
        constraints=(),
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(draft)
        with pytest.raises(DataTypePersistenceError):
            repo.replace_version(illegal)
        assert repo.get_version(datatype.id, 1) == draft


@pytest.mark.parametrize("backend", ["memory"])
def test_replace_version_allows_draft_constraint_revision(
    backend: str,
    tmp_path: Path,
) -> None:
    datatype, draft = _hostname_pair()
    revised = DataTypeVersioningService().revise_draft(
        draft,
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=2),
            Constraint(name=ConstraintName.MAX_LENGTH, value=64),
        ),
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(draft)
        repo.replace_version(revised)
        assert repo.get_version(datatype.id, 1) == revised


@pytest.mark.parametrize("backend", ["memory"])
def test_replace_version_allows_draft_to_published_status_only_transition(
    backend: str,
    tmp_path: Path,
) -> None:
    datatype, draft = _hostname_pair()
    published = DataTypeVersioningService().publish(draft)

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(draft)
        repo.replace_version(published)
        assert repo.get_version(datatype.id, 1) == published


@pytest.mark.parametrize("backend", ["memory"])
def test_replace_version_rejects_publish_with_constraint_change(
    backend: str,
    tmp_path: Path,
) -> None:
    datatype, draft = _hostname_pair()
    illegal = DataTypeVersion(
        datatype_id=draft.datatype_id,
        version=draft.version,
        status=DataTypeVersionStatus.PUBLISHED,
        base_type=draft.base_type,
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=2),),
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(draft)
        with pytest.raises(DataTypePersistenceError):
            repo.replace_version(illegal)
        assert repo.get_version(datatype.id, 1) == draft


@pytest.mark.parametrize("backend", ["memory"])
def test_replace_version_rejects_publish_with_base_type_change(
    backend: str,
    tmp_path: Path,
) -> None:
    datatype, draft = _hostname_pair()
    illegal = DataTypeVersion(
        datatype_id=draft.datatype_id,
        version=draft.version,
        status=DataTypeVersionStatus.PUBLISHED,
        base_type=PrimitiveTypeRegistry().get("core.integer"),
        constraints=(),
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(draft)
        with pytest.raises(DataTypePersistenceError):
            repo.replace_version(illegal)
        assert repo.get_version(datatype.id, 1) == draft


@pytest.mark.parametrize("backend", ["memory"])
def test_replace_version_allows_published_to_deprecated_status_only_transition(
    backend: str,
    tmp_path: Path,
) -> None:
    datatype, draft = _hostname_pair()
    published = DataTypeVersioningService().publish(draft)
    deprecated = DataTypeVersioningService().deprecate(published)

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(draft)
        repo.replace_version(published)
        repo.replace_version(deprecated)
        assert repo.get_version(datatype.id, 1) == deprecated


@pytest.mark.parametrize("backend", ["memory"])
def test_replace_version_rejects_deprecate_with_constraint_change(
    backend: str,
    tmp_path: Path,
) -> None:
    datatype, draft = _hostname_pair()
    published = DataTypeVersioningService().publish(draft)
    illegal = DataTypeVersion(
        datatype_id=published.datatype_id,
        version=published.version,
        status=DataTypeVersionStatus.DEPRECATED,
        base_type=published.base_type,
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=2),),
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(draft)
        repo.replace_version(published)
        with pytest.raises(DataTypePersistenceError):
            repo.replace_version(illegal)
        assert repo.get_version(datatype.id, 1) == published


@pytest.mark.parametrize("backend", ["memory"])
def test_replace_version_rejects_deprecate_with_base_type_change(
    backend: str,
    tmp_path: Path,
) -> None:
    datatype, draft = _hostname_pair()
    published = DataTypeVersioningService().publish(draft)
    illegal = DataTypeVersion(
        datatype_id=published.datatype_id,
        version=published.version,
        status=DataTypeVersionStatus.DEPRECATED,
        base_type=PrimitiveTypeRegistry().get("core.integer"),
        constraints=(),
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(draft)
        repo.replace_version(published)
        with pytest.raises(DataTypePersistenceError):
            repo.replace_version(illegal)
        assert repo.get_version(datatype.id, 1) == published


@pytest.mark.parametrize(
    ("stored_status", "replacement_status"),
    [
        (DataTypeVersionStatus.DRAFT, DataTypeVersionStatus.DEPRECATED),
        (DataTypeVersionStatus.PUBLISHED, DataTypeVersionStatus.PUBLISHED),
        (DataTypeVersionStatus.PUBLISHED, DataTypeVersionStatus.DRAFT),
        (DataTypeVersionStatus.DEPRECATED, DataTypeVersionStatus.DEPRECATED),
        (DataTypeVersionStatus.DEPRECATED, DataTypeVersionStatus.PUBLISHED),
        (DataTypeVersionStatus.DEPRECATED, DataTypeVersionStatus.DRAFT),
    ],
)
@pytest.mark.parametrize("backend", ["memory"])
def test_replace_version_rejects_other_lifecycle_rewrites(
    backend: str,
    tmp_path: Path,
    stored_status: DataTypeVersionStatus,
    replacement_status: DataTypeVersionStatus,
) -> None:
    datatype, draft = _hostname_pair()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        current = draft
        repo.add_version(current)
        if stored_status is DataTypeVersionStatus.PUBLISHED:
            current = DataTypeVersioningService().publish(current)
            repo.replace_version(current)
        elif stored_status is DataTypeVersionStatus.DEPRECATED:
            current = DataTypeVersioningService().publish(current)
            repo.replace_version(current)
            current = DataTypeVersioningService().deprecate(current)
            repo.replace_version(current)

        illegal = DataTypeVersion(
            datatype_id=current.datatype_id,
            version=current.version,
            status=replacement_status,
            base_type=current.base_type,
            constraints=current.constraints,
        )
        with pytest.raises(DataTypePersistenceError):
            repo.replace_version(illegal)
        assert repo.get_version(datatype.id, 1) == current


@pytest.mark.parametrize("backend", ["memory"])
def test_replace_version_missing_rejected(backend: str, tmp_path: Path) -> None:
    datatype, version = _hostname_pair()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        with pytest.raises(DataTypeVersionNotFound):
            repo.replace_version(version)


@pytest.mark.parametrize("backend", ["memory"])
def test_status_round_trip(backend: str, tmp_path: Path) -> None:
    datatype, draft = _hostname_pair()
    versioning = DataTypeVersioningService()
    v2_draft = DataTypeVersion(
        datatype_id=datatype.id,
        version=2,
        status=DataTypeVersionStatus.DRAFT,
        base_type=draft.base_type,
        constraints=draft.constraints,
    )
    v2_published = versioning.publish(v2_draft)
    v3_draft = DataTypeVersion(
        datatype_id=datatype.id,
        version=3,
        status=DataTypeVersionStatus.DRAFT,
        base_type=draft.base_type,
        constraints=draft.constraints,
    )
    v3_published = versioning.publish(v3_draft)
    v3_deprecated = versioning.deprecate(v3_published)

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(draft)
        repo.add_version(v2_draft)
        repo.replace_version(v2_published)
        repo.add_version(v3_draft)
        repo.replace_version(v3_published)
        repo.replace_version(v3_deprecated)
        loaded = repo.list_versions(datatype.id)

    assert tuple(version.status for version in loaded) == (
        DataTypeVersionStatus.DRAFT,
        DataTypeVersionStatus.PUBLISHED,
        DataTypeVersionStatus.DEPRECATED,
    )


@pytest.mark.parametrize(
    ("primitive_name", "constraints"),
    [
        ("core.string", (Constraint(name=ConstraintName.MIN_LENGTH, value=1),)),
        ("core.integer", (Constraint(name=ConstraintName.MINIMUM, value=1),)),
        ("core.number", (Constraint(name=ConstraintName.MAXIMUM, value=1.5),)),
        ("core.boolean", (Constraint(name=ConstraintName.ENUM, value=(True, False)),)),
        ("core.date", ()),
        ("core.datetime", ()),
        ("core.ip", ()),
        ("core.ip_prefix", ()),
    ],
)
@pytest.mark.parametrize("backend", ["memory"])
def test_all_primitive_names_round_trip(
    backend: str,
    tmp_path: Path,
    primitive_name: str,
    constraints: tuple[Constraint, ...],
) -> None:
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name=f"value_{primitive_name.split('.')[1]}",
        description=None,
        base_type=primitive_name,
        constraints=constraints,
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded is not None
    assert loaded.base_type is PrimitiveTypeRegistry().get(primitive_name)


@pytest.mark.parametrize("backend", ["memory"])
def test_string_constraints_round_trip(backend: str, tmp_path: Path) -> None:
    datatype, version = _hostname_pair()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded is not None
    assert loaded.constraints == version.constraints


@pytest.mark.parametrize("backend", ["memory"])
def test_integer_bounds_round_trip(backend: str, tmp_path: Path) -> None:
    datatype, version = _vlan_pair()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded == version


@pytest.mark.parametrize("backend", ["memory"])
def test_number_float_bounds_round_trip(backend: str, tmp_path: Path) -> None:
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="link_cost",
        description="Link cost",
        base_type="core.number",
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=0.5),
            Constraint(name=ConstraintName.MAXIMUM, value=100.25),
        ),
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded == version


@pytest.mark.parametrize("backend", ["memory"])
def test_boolean_enum_round_trip(backend: str, tmp_path: Path) -> None:
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="enabled",
        description=None,
        base_type="core.boolean",
        constraints=(Constraint(name=ConstraintName.ENUM, value=(True, False)),),
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded == version


@pytest.mark.parametrize("backend", ["memory"])
def test_string_enum_round_trip(backend: str, tmp_path: Path) -> None:
    datatype, version = _status_pair()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded == version


@pytest.mark.parametrize("backend", ["memory"])
def test_constraint_order_preserved(backend: str, tmp_path: Path) -> None:
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="ordered_constraints",
        description=None,
        base_type="core.string",
        constraints=(
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
            Constraint(name=ConstraintName.MIN_LENGTH, value=1),
            Constraint(name=ConstraintName.PATTERN, value=r"^[a-z0-9-]+$"),
        ),
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded is not None
    assert tuple(constraint.name for constraint in loaded.constraints) == (
        ConstraintName.MAX_LENGTH,
        ConstraintName.MIN_LENGTH,
        ConstraintName.PATTERN,
    )


def test_core_datatype_modules_remain_sqlalchemy_free() -> None:
    datatype_dir = Path("/home/alberto/NETAUTO/src/netauto/core/datatype")

    for path in datatype_dir.glob("*.py"):
        text_content = path.read_text()
        assert "import sqlalchemy" not in text_content
        assert "from sqlalchemy" not in text_content


def test_persistence_import_has_no_database_side_effects(tmp_path: Path) -> None:
    database_file = tmp_path / "side_effect.db"

    assert database_file.exists() is False
    importlib.import_module("netauto.persistence")
    importlib.import_module("netauto.persistence.sqlalchemy")
    importlib.import_module("netauto.persistence.sqlalchemy.database")
    assert database_file.exists() is False

import importlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

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
    SchemaCompiler,
    ValidationEngine,
)
from netauto.persistence.memory.datatype_repository import InMemoryDataTypeRepository
from netauto.persistence.sqlalchemy.database import create_schema, create_sqlite_engine
from netauto.persistence.sqlalchemy.datatype_repository import SqlAlchemyDataTypeRepository


@contextmanager
def _repository_harness(
    backend: str,
    tmp_path: Path,
) -> Iterator[DataTypeRepository]:
    if backend == "memory":
        yield InMemoryDataTypeRepository()
        return

    if backend != "sqlite":
        raise AssertionError(f"Unknown backend '{backend}'.")

    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'repository.sqlite3'}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield SqlAlchemyDataTypeRepository(session)
    finally:
        session.close()
        engine.dispose()


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


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_repository_datatype_round_trip(backend: str, tmp_path: Path) -> None:
    datatype = _datatype()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)

        loaded = repo.get(datatype.id)

    assert loaded == datatype


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
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
@pytest.mark.parametrize("backend", ["memory", "sqlite"])
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


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_get_by_name(backend: str, tmp_path: Path) -> None:
    datatype = _datatype()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        loaded = repo.get_by_name("network", "hostname")

    assert loaded == datatype


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
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


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
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


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_duplicate_logical_name_rejected(backend: str, tmp_path: Path) -> None:
    first = _datatype()
    second = _datatype()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(first)
        with pytest.raises(DataTypeAlreadyExists):
            repo.add(second)


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
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
    ],
)
@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_temporal_datatype_version_round_trip_preserves_primitive_metadata(
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


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
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
        repo.add_version(v5_draft)
        repo.add_version(v1_published)
        repo.add_version(v2_draft)

        versions = repo.list_versions(datatype.id)

    assert tuple(version.version for version in versions) == (1, 2, 5)


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_duplicate_version_rejected(backend: str, tmp_path: Path) -> None:
    datatype, version = _hostname_pair()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        with pytest.raises(DataTypeVersionAlreadyExists):
            repo.add_version(version)


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_missing_parent_rejected(backend: str, tmp_path: Path) -> None:
    _, version = _hostname_pair()

    with _repository_harness(backend, tmp_path) as repo:
        with pytest.raises(DataTypeNotFound):
            repo.add_version(version)


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_replace_version_existing(backend: str, tmp_path: Path) -> None:
    datatype, draft = _hostname_pair()
    service = DataTypeVersioningService()
    revised = service.revise_draft(
        draft,
        base_type=PrimitiveTypeRegistry().get("core.string"),
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


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_replace_version_missing_rejected(backend: str, tmp_path: Path) -> None:
    datatype, version = _hostname_pair()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        with pytest.raises(DataTypeVersionNotFound):
            repo.replace_version(version)


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_status_round_trip(backend: str, tmp_path: Path) -> None:
    datatype, draft = _hostname_pair()
    published = DataTypeVersion(
        datatype_id=datatype.id,
        version=2,
        status=DataTypeVersionStatus.PUBLISHED,
        base_type=draft.base_type,
        constraints=draft.constraints,
    )
    deprecated = DataTypeVersion(
        datatype_id=datatype.id,
        version=3,
        status=DataTypeVersionStatus.DEPRECATED,
        base_type=draft.base_type,
        constraints=draft.constraints,
    )

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(draft)
        repo.add_version(published)
        repo.add_version(deprecated)
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
    ],
)
@pytest.mark.parametrize("backend", ["memory", "sqlite"])
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


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_string_constraints_round_trip(backend: str, tmp_path: Path) -> None:
    datatype, version = _hostname_pair()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded is not None
    assert loaded.constraints == version.constraints


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_integer_bounds_round_trip(backend: str, tmp_path: Path) -> None:
    datatype, version = _vlan_pair()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded == version


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
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


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
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


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_string_enum_round_trip(backend: str, tmp_path: Path) -> None:
    datatype, version = _status_pair()

    with _repository_harness(backend, tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded == version


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
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


def test_sqlite_large_integer_round_trip(tmp_path: Path) -> None:
    large_integer = 10**1000
    datatype, version = DataTypeFactory().create(
        namespace="network",
        name="huge_minimum",
        description=None,
        base_type="core.number",
        constraints=(Constraint(name=ConstraintName.MINIMUM, value=large_integer),),
    )

    with _repository_harness("sqlite", tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded is not None
    assert loaded.constraints[0].value == large_integer
    assert type(loaded.constraints[0].value) is int
    assert SchemaCompiler().compile_datatype(loaded) == {
        "type": "number",
        "minimum": large_integer,
    }


def test_compiler_works_after_sqlite_reload(tmp_path: Path) -> None:
    datatype, version = _vlan_pair()

    with _repository_harness("sqlite", tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded is not None
    assert SchemaCompiler().compile_datatype(loaded) == {
        "type": "integer",
        "minimum": 1,
        "maximum": 4094,
    }


def test_validation_works_after_sqlite_reload(tmp_path: Path) -> None:
    datatype, version = _vlan_pair()

    with _repository_harness("sqlite", tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(version)
        loaded = repo.get_version(datatype.id, 1)

    assert loaded is not None
    engine = ValidationEngine()
    assert engine.validate_datatype(loaded, 1).is_valid is True
    assert engine.validate_datatype(loaded, 4094).is_valid is True
    assert engine.validate_datatype(loaded, 0).errors == (
        engine.validate_datatype(loaded, 0).errors[0],
    )
    assert engine.validate_datatype(loaded, 4095).errors == (
        engine.validate_datatype(loaded, 4095).errors[0],
    )
    assert engine.validate_datatype(loaded, 1.0).errors[0].code == "type"
    assert engine.validate_datatype(loaded, True).errors[0].code == "type"


def test_versioning_service_works_across_persisted_snapshots(tmp_path: Path) -> None:
    datatype, v1_draft = _vlan_pair()
    service = DataTypeVersioningService()

    with _repository_harness("sqlite", tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(v1_draft)
        loaded_draft = repo.get_version(datatype.id, 1)
        assert loaded_draft is not None
        v1_published = service.publish(loaded_draft)
        repo.replace_version(v1_published)
        v2_draft = service.create_next_version(v1_published, existing_versions=(v1_published,))
        repo.add_version(v2_draft)
        v2_published = service.publish(v2_draft)
        repo.replace_version(v2_published)
        versions = repo.list_versions(datatype.id)

    assert tuple((version.version, version.status) for version in versions) == (
        (1, DataTypeVersionStatus.PUBLISHED),
        (2, DataTypeVersionStatus.PUBLISHED),
    )


def test_multiple_published_versions_coexist_in_repository(tmp_path: Path) -> None:
    datatype, v1_draft = _hostname_pair()
    service = DataTypeVersioningService()
    v1_published = service.publish(v1_draft)
    v2_draft = service.create_next_version(v1_published, existing_versions=(v1_published,))
    v2_published = service.publish(v2_draft)

    with _repository_harness("sqlite", tmp_path) as repo:
        repo.add(datatype)
        repo.add_version(v1_draft)
        repo.replace_version(v1_published)
        repo.add_version(v2_draft)
        repo.replace_version(v2_published)
        versions = repo.list_versions(datatype.id)

    assert tuple(version.status for version in versions) == (
        DataTypeVersionStatus.PUBLISHED,
        DataTypeVersionStatus.PUBLISHED,
    )


def test_sqlite_foreign_key_enforcement_is_active(tmp_path: Path) -> None:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'fk.sqlite3'}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    try:
        with pytest.raises(IntegrityError):
            session.execute(
                text(
                    "INSERT INTO datatype_versions "
                    "(datatype_id, version, status, base_type, constraints_json) "
                    "VALUES (:datatype_id, :version, :status, :base_type, :constraints_json)"
                ),
                {
                    "datatype_id": str(UUID(int=1)),
                    "version": 1,
                    "status": "draft",
                    "base_type": "core.string",
                    "constraints_json": "[]",
                },
            )
            session.commit()
    finally:
        session.close()
        engine.dispose()


def test_sqlite_constraint_json_is_deterministic_text(tmp_path: Path) -> None:
    datatype, version = _status_pair()
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'json.sqlite3'}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    try:
        repo = SqlAlchemyDataTypeRepository(session)
        repo.add(datatype)
        repo.add_version(version)
        stored = session.execute(
            text(
                "SELECT constraints_json FROM datatype_versions "
                "WHERE datatype_id = :datatype_id AND version = :version"
            ),
            {"datatype_id": str(datatype.id), "version": 1},
        ).scalar_one()
    finally:
        session.close()
        engine.dispose()

    assert stored == json.dumps(
        [{"name": "enum", "value": ["active", "planned", "retired"]}],
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


@pytest.mark.parametrize(
    ("constraints_json", "status", "base_type"),
    [
        ("{", "draft", "core.string"),
        ('{"name":"minimum","value":1}', "draft", "core.string"),
        ('[{"name":"minimum"}]', "draft", "core.string"),
        ('[{"name":"unknown","value":1}]', "draft", "core.string"),
        ("[]", "unknown", "core.string"),
        ("[]", "draft", "core.unknown"),
    ],
)
def test_sqlite_corrupt_version_rows_raise_persistence_error(
    tmp_path: Path,
    constraints_json: str,
    status: str,
    base_type: str,
) -> None:
    datatype = _datatype()
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'corrupt.sqlite3'}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    try:
        session.execute(
            text(
                "INSERT INTO datatypes (id, namespace, name, description) "
                "VALUES (:id, :namespace, :name, :description)"
            ),
            {
                "id": str(datatype.id),
                "namespace": datatype.namespace,
                "name": datatype.name,
                "description": datatype.description,
            },
        )
        session.execute(
            text(
                "INSERT INTO datatype_versions "
                "(datatype_id, version, status, base_type, constraints_json) "
                "VALUES (:datatype_id, :version, :status, :base_type, :constraints_json)"
            ),
            {
                "datatype_id": str(datatype.id),
                "version": 1,
                "status": status,
                "base_type": base_type,
                "constraints_json": constraints_json,
            },
        )
        session.commit()
        repo = SqlAlchemyDataTypeRepository(session)
        with pytest.raises(DataTypePersistenceError):
            repo.get_version(datatype.id, 1)
    finally:
        session.close()
        engine.dispose()


def test_sqlite_invalid_uuid_row_raises_persistence_error(tmp_path: Path) -> None:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'bad_uuid.sqlite3'}")
    create_schema(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    try:
        session.execute(
            text(
                "INSERT INTO datatypes (id, namespace, name, description) "
                "VALUES ('not-a-uuid', 'network', 'hostname', NULL)"
            )
        )
        session.commit()
        repo = SqlAlchemyDataTypeRepository(session)
        with pytest.raises(DataTypePersistenceError):
            repo.get_by_name("network", "hostname")
    finally:
        session.close()
        engine.dispose()


def test_core_datatype_modules_remain_sqlalchemy_free() -> None:
    datatype_dir = Path("/home/alberto/NETAUTO/src/netauto/core/datatype")

    for path in datatype_dir.glob("*.py"):
        text_content = path.read_text()
        assert "import sqlalchemy" not in text_content
        assert "from sqlalchemy" not in text_content


def test_persistence_import_has_no_database_side_effects(tmp_path: Path) -> None:
    database_file = tmp_path / "side_effect.sqlite3"

    assert database_file.exists() is False
    importlib.import_module("netauto.persistence")
    importlib.import_module("netauto.persistence.sqlalchemy")
    importlib.import_module("netauto.persistence.sqlalchemy.database")
    assert database_file.exists() is False

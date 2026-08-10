from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataTypeFactory,
    DataTypeVersion,
    DataTypeVersioningService,
    DataTypeVersionStatus,
    InvalidConstraintValue,
    InvalidDataTypeVersionTransition,
    MismatchedDataTypeVersion,
    PrimitiveTypeRegistry,
    SchemaCompilationError,
    SchemaCompiler,
    ValidationEngine,
)


def _base_type(name: str):
    return PrimitiveTypeRegistry().get(name)


def _draft_version() -> DataTypeVersion:
    return DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.integer"),
        constraints=(Constraint(name=ConstraintName.MINIMUM, value=1),),
    )


def test_datatype_version_is_immutable() -> None:
    version = _draft_version()

    with pytest.raises(FrozenInstanceError):
        version.status = DataTypeVersionStatus.PUBLISHED  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        version.base_type = _base_type("core.string")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        version.constraints = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        version.version = 2  # type: ignore[misc]


def test_datatype_version_still_validates_constraints_and_normalizes_tuple() -> None:
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=DataTypeVersionStatus.DRAFT,
        base_type=_base_type("core.string"),
        constraints=(Constraint(name=ConstraintName.MIN_LENGTH, value=1),),
    )

    assert version.constraints == (Constraint(name=ConstraintName.MIN_LENGTH, value=1),)
    assert isinstance(version.constraints, tuple)


def test_revise_draft_returns_replacement_snapshot() -> None:
    service = DataTypeVersioningService()
    original = _draft_version()

    revised = service.revise_draft(
        original,
        constraints=(Constraint(name=ConstraintName.MAXIMUM, value=4094),),
    )

    assert revised.datatype_id == original.datatype_id
    assert revised.version == original.version
    assert revised.status is DataTypeVersionStatus.DRAFT
    assert revised.base_type == original.base_type
    assert revised.constraints == (Constraint(name=ConstraintName.MAXIMUM, value=4094),)
    assert original.base_type.name == "core.integer"
    assert original.constraints == (Constraint(name=ConstraintName.MINIMUM, value=1),)


@pytest.mark.parametrize(
    "status",
    [DataTypeVersionStatus.PUBLISHED, DataTypeVersionStatus.DEPRECATED],
)
def test_revise_draft_rejects_non_draft_versions(status: DataTypeVersionStatus) -> None:
    service = DataTypeVersioningService()
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=status,
        base_type=_base_type("core.integer"),
        constraints=(),
    )

    with pytest.raises(InvalidDataTypeVersionTransition):
        service.revise_draft(
            version,
            constraints=(),
        )


def test_revise_draft_propagates_constraint_validation_errors() -> None:
    service = DataTypeVersioningService()

    with pytest.raises(InvalidConstraintValue):
        service.revise_draft(
            _draft_version(),
            constraints=(Constraint(name=ConstraintName.MINIMUM, value=True),),
        )


def test_publish_transitions_draft_to_published() -> None:
    service = DataTypeVersioningService()
    draft = _draft_version()

    published = service.publish(draft)

    assert published.datatype_id == draft.datatype_id
    assert published.version == draft.version
    assert published.status is DataTypeVersionStatus.PUBLISHED
    assert published.base_type == draft.base_type
    assert published.constraints == draft.constraints
    assert draft.status is DataTypeVersionStatus.DRAFT


@pytest.mark.parametrize(
    "status",
    [DataTypeVersionStatus.PUBLISHED, DataTypeVersionStatus.DEPRECATED],
)
def test_publish_rejects_non_draft_versions(status: DataTypeVersionStatus) -> None:
    service = DataTypeVersioningService()
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=status,
        base_type=_base_type("core.integer"),
        constraints=(),
    )

    with pytest.raises(InvalidDataTypeVersionTransition):
        service.publish(version)


def test_publish_propagates_schema_compilation_error_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = DataTypeVersioningService()

    def broken_compile(_version: DataTypeVersion) -> dict[str, object]:
        raise SchemaCompilationError("broken schema")

    monkeypatch.setattr(service._compiler, "compile_datatype", broken_compile)

    with pytest.raises(SchemaCompilationError):
        service.publish(_draft_version())


def test_deprecate_transitions_published_to_deprecated() -> None:
    service = DataTypeVersioningService()
    published = service.publish(_draft_version())

    deprecated = service.deprecate(published)

    assert deprecated.datatype_id == published.datatype_id
    assert deprecated.version == published.version
    assert deprecated.status is DataTypeVersionStatus.DEPRECATED
    assert deprecated.base_type == published.base_type
    assert deprecated.constraints == published.constraints
    assert published.status is DataTypeVersionStatus.PUBLISHED


@pytest.mark.parametrize(
    "status",
    [DataTypeVersionStatus.DRAFT, DataTypeVersionStatus.DEPRECATED],
)
def test_deprecate_rejects_non_published_versions(status: DataTypeVersionStatus) -> None:
    service = DataTypeVersioningService()
    version = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=status,
        base_type=_base_type("core.integer"),
        constraints=(),
    )

    with pytest.raises(InvalidDataTypeVersionTransition):
        service.deprecate(version)


def test_create_next_version_creates_v2_draft_from_published_source() -> None:
    service = DataTypeVersioningService()
    source = service.publish(_draft_version())

    next_version = service.create_next_version(source, existing_versions=(source,))

    assert next_version.datatype_id == source.datatype_id
    assert next_version.version == 2
    assert next_version.status is DataTypeVersionStatus.DRAFT
    assert next_version.base_type == source.base_type
    assert next_version.constraints == source.constraints
    assert source.version == 1
    assert source.status is DataTypeVersionStatus.PUBLISHED


def test_create_next_version_creates_draft_from_deprecated_source_without_mutating_source() -> None:
    service = DataTypeVersioningService()
    published = service.publish(_draft_version())
    deprecated = service.deprecate(published)

    next_version = service.create_next_version(
        deprecated,
        existing_versions=(published, deprecated),
    )

    assert next_version.datatype_id == deprecated.datatype_id
    assert next_version.version == 2
    assert next_version.status is DataTypeVersionStatus.DRAFT
    assert next_version.base_type == deprecated.base_type
    assert next_version.constraints == deprecated.constraints
    assert deprecated.version == 1
    assert deprecated.status is DataTypeVersionStatus.DEPRECATED
    assert deprecated.base_type == published.base_type
    assert deprecated.constraints == published.constraints


def test_create_next_version_uses_monotonic_max_existing_plus_one() -> None:
    service = DataTypeVersioningService()
    datatype_id = uuid4()
    source = DataTypeVersion(
        datatype_id=datatype_id,
        version=1,
        status=DataTypeVersionStatus.PUBLISHED,
        base_type=_base_type("core.integer"),
        constraints=(Constraint(name=ConstraintName.MINIMUM, value=1),),
    )
    existing_versions = (
        source,
        DataTypeVersion(
            datatype_id=datatype_id,
            version=2,
            status=DataTypeVersionStatus.PUBLISHED,
            base_type=source.base_type,
            constraints=source.constraints,
        ),
        DataTypeVersion(
            datatype_id=datatype_id,
            version=5,
            status=DataTypeVersionStatus.DEPRECATED,
            base_type=source.base_type,
            constraints=source.constraints,
        ),
    )

    next_version = service.create_next_version(source, existing_versions=existing_versions)

    assert next_version.version == 6


def test_create_next_version_supports_generator_existing_versions() -> None:
    service = DataTypeVersioningService()
    datatype_id = uuid4()
    v1 = DataTypeVersion(
        datatype_id=datatype_id,
        version=1,
        status=DataTypeVersionStatus.PUBLISHED,
        base_type=_base_type("core.integer"),
        constraints=(Constraint(name=ConstraintName.MINIMUM, value=1),),
    )
    v2 = DataTypeVersion(
        datatype_id=datatype_id,
        version=2,
        status=DataTypeVersionStatus.PUBLISHED,
        base_type=v1.base_type,
        constraints=v1.constraints,
    )
    v5 = DataTypeVersion(
        datatype_id=datatype_id,
        version=5,
        status=DataTypeVersionStatus.DEPRECATED,
        base_type=v1.base_type,
        constraints=v1.constraints,
    )
    existing_versions = (version for version in (v1, v2, v5))

    next_version = service.create_next_version(v1, existing_versions=existing_versions)

    assert next_version.version == 6
    assert next_version.status is DataTypeVersionStatus.DRAFT


def test_create_next_version_from_deprecated_source_uses_max_existing_plus_one() -> None:
    service = DataTypeVersioningService()
    datatype_id = uuid4()
    source = DataTypeVersion(
        datatype_id=datatype_id,
        version=1,
        status=DataTypeVersionStatus.DEPRECATED,
        base_type=_base_type("core.integer"),
        constraints=(Constraint(name=ConstraintName.MINIMUM, value=1),),
    )
    existing_versions = (
        source,
        DataTypeVersion(
            datatype_id=datatype_id,
            version=3,
            status=DataTypeVersionStatus.DEPRECATED,
            base_type=source.base_type,
            constraints=source.constraints,
        ),
    )

    next_version = service.create_next_version(source, existing_versions=existing_versions)

    assert next_version.version == 4
    assert next_version.base_type == source.base_type
    assert next_version.constraints == source.constraints


@pytest.mark.parametrize(
    "status",
    [DataTypeVersionStatus.DRAFT],
)
def test_create_next_version_rejects_non_published_sources(status: DataTypeVersionStatus) -> None:
    service = DataTypeVersioningService()
    source = DataTypeVersion(
        datatype_id=uuid4(),
        version=1,
        status=status,
        base_type=_base_type("core.integer"),
        constraints=(),
    )

    with pytest.raises(InvalidDataTypeVersionTransition):
        service.create_next_version(source, existing_versions=(source,))


def test_create_next_version_rejects_mismatched_datatype_ids() -> None:
    service = DataTypeVersioningService()
    source = service.publish(_draft_version())
    other = DataTypeVersion(
        datatype_id=uuid4(),
        version=2,
        status=DataTypeVersionStatus.PUBLISHED,
        base_type=source.base_type,
        constraints=source.constraints,
    )

    with pytest.raises(MismatchedDataTypeVersion):
        service.create_next_version(source, existing_versions=(source, other))


def test_create_next_version_rejects_mismatched_datatype_ids_from_generator() -> None:
    service = DataTypeVersioningService()
    source = service.publish(_draft_version())
    other = DataTypeVersion(
        datatype_id=uuid4(),
        version=2,
        status=DataTypeVersionStatus.PUBLISHED,
        base_type=source.base_type,
        constraints=source.constraints,
    )
    existing_versions = (version for version in (source, other))

    with pytest.raises(MismatchedDataTypeVersion):
        service.create_next_version(source, existing_versions=existing_versions)


def test_create_next_version_accepts_empty_existing_versions() -> None:
    service = DataTypeVersioningService()
    source = DataTypeVersion(
        datatype_id=uuid4(),
        version=3,
        status=DataTypeVersionStatus.PUBLISHED,
        base_type=_base_type("core.integer"),
        constraints=(Constraint(name=ConstraintName.MINIMUM, value=1),),
    )

    next_version = service.create_next_version(source, existing_versions=())

    assert next_version.version == 4
    assert next_version.status is DataTypeVersionStatus.DRAFT


def test_no_automatic_deprecation_when_publishing_newer_version() -> None:
    service = DataTypeVersioningService()
    v1_published = service.publish(_draft_version())
    v2_draft = service.create_next_version(v1_published, existing_versions=(v1_published,))
    v2_published = service.publish(v2_draft)

    assert v1_published.status is DataTypeVersionStatus.PUBLISHED
    assert v2_published.status is DataTypeVersionStatus.PUBLISHED


def test_multiple_published_versions_may_coexist() -> None:
    service = DataTypeVersioningService()
    v1_published = service.publish(_draft_version())
    v2_draft = service.create_next_version(v1_published, existing_versions=(v1_published,))
    v2_published = service.publish(v2_draft)

    assert v1_published.status is DataTypeVersionStatus.PUBLISHED
    assert v2_published.status is DataTypeVersionStatus.PUBLISHED
    assert v1_published.version == 1
    assert v2_published.version == 2


def test_factory_integration_through_versioning_flow() -> None:
    datatype, v1_draft = DataTypeFactory().create(
        namespace="network",
        name="vlan_id",
        description="VLAN identifier",
        base_type="core.integer",
        constraints=(
            Constraint(name=ConstraintName.MINIMUM, value=1),
            Constraint(name=ConstraintName.MAXIMUM, value=4094),
        ),
    )
    service = DataTypeVersioningService()

    v1_published = service.publish(v1_draft)
    v2_draft = service.create_next_version(v1_published, existing_versions=(v1_published,))

    assert v1_draft.datatype_id == datatype.id
    assert v1_published.datatype_id == datatype.id
    assert v2_draft.datatype_id == datatype.id
    assert v2_draft.version == 2


def test_compiler_and_validator_work_with_versioning_outputs() -> None:
    datatype, v1_draft = DataTypeFactory().create(
        namespace="network",
        name="hostname",
        description="Network hostname",
        base_type="core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=1),
            Constraint(name=ConstraintName.MAX_LENGTH, value=253),
        ),
    )
    service = DataTypeVersioningService()
    v1_published = service.publish(v1_draft)
    v2_draft = service.create_next_version(v1_published, existing_versions=(v1_published,))

    schema = SchemaCompiler().compile_datatype(v2_draft)
    validation = ValidationEngine().validate_datatype(v2_draft, "router01")

    assert datatype.id == v2_draft.datatype_id
    assert schema == {"type": "string", "minLength": 1, "maxLength": 253}
    assert validation.is_valid is True

from dataclasses import FrozenInstanceError
from uuid import UUID, uuid4

import pytest

from netauto.core.datatype import (
    Constraint,
    ConstraintName,
    DataTypeVersion,
    DataTypeVersionStatus,
    PrimitiveTypeRegistry,
)
from netauto.core.object import (
    ObjectDataTypeVersionNotFound,
    ObjectValidationEngine,
    ObjectValidationIssue,
    ObjectValidationResult,
)
from netauto.core.objecttemplate import ObjectTemplateProperty


def _base_type(name: str):
    return PrimitiveTypeRegistry().get(name)


def _datatype_version(
    primitive_name: str,
    *,
    datatype_id: UUID | None = None,
    version: int = 1,
    status: DataTypeVersionStatus = DataTypeVersionStatus.DRAFT,
    constraints: tuple[Constraint, ...] = (),
) -> DataTypeVersion:
    return DataTypeVersion(
        datatype_id=datatype_id or uuid4(),
        version=version,
        status=status,
        base_type=_base_type(primitive_name),
        constraints=constraints,
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


def _lookup_for(
    *datatype_versions: DataTypeVersion,
):
    by_identity = {
        (datatype_version.datatype_id, datatype_version.version): datatype_version
        for datatype_version in datatype_versions
    }

    def lookup(datatype_id: UUID, version: int) -> DataTypeVersion | None:
        return by_identity.get((datatype_id, version))

    return lookup


def test_object_validation_result_empty_errors_means_valid() -> None:
    result = ObjectValidationResult()

    assert result.errors == ()
    assert result.is_valid is True


def test_object_validation_result_with_errors_means_invalid() -> None:
    result = ObjectValidationResult(
        errors=(
            ObjectValidationIssue(
                path=("properties", "hostname"),
                code="required",
                message="Required property is missing",
            ),
        )
    )

    assert result.is_valid is False


def test_object_validation_types_are_immutable() -> None:
    issue = ObjectValidationIssue(
        path=("properties", "hostname"),
        code="required",
        message="Required property is missing",
    )
    result = ObjectValidationResult(errors=(issue,))

    with pytest.raises(FrozenInstanceError):
        issue.code = "type"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.errors = ()  # type: ignore[misc]


def test_empty_template_and_empty_properties_are_valid() -> None:
    result = ObjectValidationEngine().validate_properties(
        properties={},
        effective_properties=(),
        datatype_lookup=_lookup_for(),
    )

    assert result.is_valid is True
    assert result.errors == ()


def test_required_property_present_is_valid() -> None:
    datatype_version = _datatype_version("core.string")
    result = ObjectValidationEngine().validate_properties(
        properties={"hostname": "router-01"},
        effective_properties=(
            _property(
                "hostname",
                datatype_id=datatype_version.datatype_id,
                required=True,
            ),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.is_valid is True


def test_required_property_missing_produces_required_issue() -> None:
    datatype_version = _datatype_version("core.string")
    result = ObjectValidationEngine().validate_properties(
        properties={},
        effective_properties=(
            _property(
                "hostname",
                datatype_id=datatype_version.datatype_id,
                required=True,
            ),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.errors == (
        ObjectValidationIssue(
            path=("properties", "hostname"),
            code="required",
            message="Required property is missing",
        ),
    )


def test_optional_property_may_be_omitted() -> None:
    datatype_version = _datatype_version("core.string")
    result = ObjectValidationEngine().validate_properties(
        properties={},
        effective_properties=(
            _property(
                "serial",
                datatype_id=datatype_version.datatype_id,
                required=False,
            ),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.is_valid is True


def test_unknown_property_produces_unknown_property_issue() -> None:
    result = ObjectValidationEngine().validate_properties(
        properties={"banana": "yellow"},
        effective_properties=(),
        datatype_lookup=_lookup_for(),
    )

    assert result.errors == (
        ObjectValidationIssue(
            path=("properties", "banana"),
            code="unknown_property",
            message="Property is not defined in template",
        ),
    )


def test_known_value_delegates_to_datatype_validation_engine() -> None:
    datatype_version = _datatype_version("core.string")
    result = ObjectValidationEngine().validate_properties(
        properties={"hostname": "router-01"},
        effective_properties=(
            _property("hostname", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.is_valid is True


def test_wrong_primitive_type_is_surfaced_with_prefixed_object_path() -> None:
    datatype_version = _datatype_version("core.string")
    result = ObjectValidationEngine().validate_properties(
        properties={"hostname": 123},
        effective_properties=(
            _property("hostname", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.errors == (
        ObjectValidationIssue(
            path=("properties", "hostname"),
            code="type",
            message="Value is not of the expected type",
        ),
    )


def test_datatype_constraints_are_surfaced_without_reimplementation() -> None:
    datatype_version = _datatype_version(
        "core.string",
        constraints=(
            Constraint(name=ConstraintName.MIN_LENGTH, value=2),
            Constraint(name=ConstraintName.PATTERN, value=r"^[a-z]+$"),
        ),
    )
    result = ObjectValidationEngine().validate_properties(
        properties={"hostname": ""},
        effective_properties=(
            _property("hostname", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.errors == (
        ObjectValidationIssue(
            path=("properties", "hostname"),
            code="min_length",
            message="Value is shorter than the minimum allowed length",
        ),
        ObjectValidationIssue(
            path=("properties", "hostname"),
            code="pattern",
            message="Value does not match the required pattern",
        ),
    )


def test_date_property_validation_uses_existing_datatype_validation_path() -> None:
    datatype_version = _datatype_version("core.date")
    result = ObjectValidationEngine().validate_properties(
        properties={"installation_date": "2026-08-10"},
        effective_properties=(
            _property("installation_date", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.is_valid is True


def test_invalid_date_property_surfaces_format_error_with_property_path() -> None:
    datatype_version = _datatype_version("core.date")
    result = ObjectValidationEngine().validate_properties(
        properties={"installation_date": "2026-02-31"},
        effective_properties=(
            _property("installation_date", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.errors == (
        ObjectValidationIssue(
            path=("properties", "installation_date"),
            code="format",
            message="Value does not match the required format",
        ),
    )


def test_datetime_property_validation_uses_existing_datatype_validation_path() -> None:
    datatype_version = _datatype_version("core.datetime")
    result = ObjectValidationEngine().validate_properties(
        properties={"last_seen": "2026-08-10T15:14:00Z"},
        effective_properties=(
            _property("last_seen", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.is_valid is True


def test_invalid_datetime_property_surfaces_format_error_with_property_path() -> None:
    datatype_version = _datatype_version("core.datetime")
    result = ObjectValidationEngine().validate_properties(
        properties={"last_seen": "2026-08-10T15:14:00"},
        effective_properties=(
            _property("last_seen", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.errors == (
        ObjectValidationIssue(
            path=("properties", "last_seen"),
            code="format",
            message="Value does not match the required format",
        ),
    )


@pytest.mark.parametrize("value", ["192.0.2.10", "2001:db8::10"])
def test_ip_property_validation_uses_existing_datatype_validation_path(value: str) -> None:
    datatype_version = _datatype_version("core.ip")
    result = ObjectValidationEngine().validate_properties(
        properties={"management_ip": value},
        effective_properties=(
            _property("management_ip", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.is_valid is True


@pytest.mark.parametrize("value", ["192.0.2.999", "192.0.2.10/24"])
def test_invalid_ip_property_surfaces_format_error_with_property_path(value: str) -> None:
    datatype_version = _datatype_version("core.ip")
    result = ObjectValidationEngine().validate_properties(
        properties={"management_ip": value},
        effective_properties=(
            _property("management_ip", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.errors == (
        ObjectValidationIssue(
            path=("properties", "management_ip"),
            code="format",
            message="Value does not match the required format",
        ),
    )


@pytest.mark.parametrize("value", ["192.0.2.0/24", "2001:db8:100::/48"])
def test_ip_prefix_property_validation_uses_existing_datatype_validation_path(value: str) -> None:
    datatype_version = _datatype_version("core.ip_prefix")
    result = ObjectValidationEngine().validate_properties(
        properties={"connected_prefix": value},
        effective_properties=(
            _property("connected_prefix", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.is_valid is True


@pytest.mark.parametrize("value", ["192.0.2.10/24", "2001:db8:100::1/48"])
def test_invalid_ip_prefix_property_surfaces_format_error_with_property_path(value: str) -> None:
    datatype_version = _datatype_version("core.ip_prefix")
    result = ObjectValidationEngine().validate_properties(
        properties={"connected_prefix": value},
        effective_properties=(
            _property("connected_prefix", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.errors == (
        ObjectValidationIssue(
            path=("properties", "connected_prefix"),
            code="format",
            message="Value does not match the required format",
        ),
    )


def test_multiple_independent_errors_are_collected_in_deterministic_order() -> None:
    hostname_datatype = _datatype_version("core.string")
    serial_datatype = _datatype_version("core.string")
    result = ObjectValidationEngine().validate_properties(
        properties={
            "serial": 123,
            "banana": "yellow",
        },
        effective_properties=(
            _property(
                "hostname",
                datatype_id=hostname_datatype.datatype_id,
                required=True,
            ),
            _property("serial", datatype_id=serial_datatype.datatype_id),
        ),
        datatype_lookup=_lookup_for(hostname_datatype, serial_datatype),
    )

    assert result.errors == (
        ObjectValidationIssue(
            path=("properties", "banana"),
            code="unknown_property",
            message="Property is not defined in template",
        ),
        ObjectValidationIssue(
            path=("properties", "hostname"),
            code="required",
            message="Required property is missing",
        ),
        ObjectValidationIssue(
            path=("properties", "serial"),
            code="type",
            message="Value is not of the expected type",
        ),
    )


def test_exact_datatype_uuid_and_version_are_used() -> None:
    datatype_id = uuid4()
    datatype_v1 = _datatype_version("core.integer", datatype_id=datatype_id, version=1)
    datatype_v2 = _datatype_version("core.string", datatype_id=datatype_id, version=2)
    calls: list[tuple[UUID, int]] = []

    def lookup(requested_datatype_id: UUID, requested_version: int) -> DataTypeVersion | None:
        calls.append((requested_datatype_id, requested_version))
        return {
            (datatype_v1.datatype_id, datatype_v1.version): datatype_v1,
            (datatype_v2.datatype_id, datatype_v2.version): datatype_v2,
        }.get((requested_datatype_id, requested_version))

    result = ObjectValidationEngine().validate_properties(
        properties={"hostname": "router-01"},
        effective_properties=(
            _property("hostname", datatype_id=datatype_id, datatype_version=2),
        ),
        datatype_lookup=lookup,
    )

    assert result.is_valid is True
    assert calls == [(datatype_id, 2)]


def test_missing_exact_datatype_version_raises_object_domain_exception() -> None:
    datatype_id = uuid4()

    with pytest.raises(ObjectDataTypeVersionNotFound):
        ObjectValidationEngine().validate_properties(
            properties={"hostname": "router-01"},
            effective_properties=(
                _property("hostname", datatype_id=datatype_id, datatype_version=2),
            ),
            datatype_lookup=lambda _datatype_id, _version: None,
        )


def test_no_fallback_to_other_existing_datatype_version() -> None:
    datatype_id = uuid4()
    datatype_v1 = _datatype_version("core.string", datatype_id=datatype_id, version=1)

    with pytest.raises(ObjectDataTypeVersionNotFound):
        ObjectValidationEngine().validate_properties(
            properties={"hostname": "router-01"},
            effective_properties=(
                _property("hostname", datatype_id=datatype_id, datatype_version=2),
            ),
            datatype_lookup=_lookup_for(datatype_v1),
        )


def test_deprecated_exact_datatype_version_is_still_used_successfully() -> None:
    datatype_version = _datatype_version(
        "core.string",
        status=DataTypeVersionStatus.DEPRECATED,
    )
    result = ObjectValidationEngine().validate_properties(
        properties={"hostname": "router-01"},
        effective_properties=(
            _property("hostname", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.is_valid is True


def test_none_is_delegated_as_runtime_value() -> None:
    datatype_version = _datatype_version("core.string")
    result = ObjectValidationEngine().validate_properties(
        properties={"hostname": None},
        effective_properties=(
            _property("hostname", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.errors == (
        ObjectValidationIssue(
            path=("properties", "hostname"),
            code="type",
            message="Value is not of the expected type",
        ),
    )


@pytest.mark.parametrize("primitive_name", ["core.integer", "core.number"])
def test_bool_is_rejected_when_referenced_datatype_is_integer_or_number(
    primitive_name: str,
) -> None:
    datatype_version = _datatype_version(primitive_name)
    result = ObjectValidationEngine().validate_properties(
        properties={"metric": True},
        effective_properties=(
            _property("metric", datatype_id=datatype_version.datatype_id),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.errors == (
        ObjectValidationIssue(
            path=("properties", "metric"),
            code="type",
            message="Value is not of the expected type",
        ),
    )


def test_effective_property_declarations_are_validated_without_resolving_inheritance() -> None:
    datatype_version = _datatype_version("core.string")
    result = ObjectValidationEngine().validate_properties(
        properties={"hostname": "router-01"},
        effective_properties=(
            _property(
                "hostname",
                datatype_id=datatype_version.datatype_id,
                required=True,
            ),
        ),
        datatype_lookup=_lookup_for(datatype_version),
    )

    assert result.is_valid is True

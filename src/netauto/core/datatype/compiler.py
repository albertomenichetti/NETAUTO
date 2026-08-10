"""Compile datatype versions to JSON Schema fragments."""

from typing import cast

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from netauto.core.datatype.constraints import ConstraintName
from netauto.core.datatype.exceptions import SchemaCompilationError
from netauto.core.datatype.models import DataTypeVersion

_SCHEMA_KEYWORDS = {
    ConstraintName.MIN_LENGTH: "minLength",
    ConstraintName.MAX_LENGTH: "maxLength",
    ConstraintName.PATTERN: "pattern",
    ConstraintName.MINIMUM: "minimum",
    ConstraintName.MAXIMUM: "maximum",
    ConstraintName.ENUM: "enum",
}


class SchemaCompiler:
    """Compile datatype versions into JSON Schema Draft 2020-12 fragments."""

    def compile_datatype(self, datatype_version: DataTypeVersion) -> dict[str, object]:
        schema: dict[str, object] = {"type": datatype_version.base_type.json_schema_type}
        if datatype_version.base_type.json_schema_format is not None:
            schema["format"] = datatype_version.base_type.json_schema_format

        for constraint in datatype_version.constraints:
            keyword = _SCHEMA_KEYWORDS.get(constraint.name)
            if keyword is None:
                raise SchemaCompilationError(
                    f"No JSON Schema mapping exists for constraint '{constraint.name.value}'."
                )
            if constraint.name is ConstraintName.ENUM:
                schema[keyword] = list(cast("tuple[object, ...]", constraint.value))
            else:
                schema[keyword] = constraint.value

        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as error:
            raise SchemaCompilationError("Generated schema is not valid Draft 2020-12.") from error

        return schema

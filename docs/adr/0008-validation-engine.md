# ADR 0008: Validation Engine

## Status

Accepted

## Context

NETAUTO needs runtime value validation for `DataTypeVersion` definitions while
keeping schema compilation and runtime validation as separate responsibilities.

## Decision

ValidationEngine validates `DataTypeVersion` runtime values through
SchemaCompiler. JSON Schema Draft 2020-12 and `python-jsonschema` remain the
validation engine. Invalid user data returns a structured ValidationResult
rather than raising. ValidationIssue is a NETAUTO-owned representation, and
`jsonschema` ValidationError does not cross the core boundary. `core.integer`
uses strict runtime integer representation and rejects integral floats such as
`1.0`. `bool` is never accepted as integer or number. `core.number` accepts
only finite `int` and `float` JSON-native numeric representations. `NaN` and
infinities are rejected. Validation performs no coercion. Nullability remains
outside DataType and `None` is invalid here. JSON Schema validator keywords are
mapped back to NETAUTO snake_case validation codes. Validation messages are
NETAUTO-owned rather than raw library messages. All validation errors are
collected. Validation is independent of DataTypeVersion lifecycle status.
SchemaCompilationError remains distinct from ValidationEngineError.

## Consequences

Runtime validation stays aligned with compiled schemas while preserving strict
NETAUTO type semantics and a stable domain-facing error surface.

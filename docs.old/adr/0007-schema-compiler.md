# ADR 0007: Schema Compiler

## Status

Accepted

## Context

NETAUTO needs to compile primitive-based `DataTypeVersion` definitions into
JSON Schema without coupling the domain model to JSON Schema keyword names.

## Decision

`DataTypeVersion` is compiled to JSON Schema Draft 2020-12. SchemaCompiler
produces schema fragments rather than complete root schema documents, so
fragments intentionally omit `$schema`, `$id`, and NETAUTO metadata. Root
schema wrapping belongs to later export and template functionality. Domain
constraint names are translated by SchemaCompiler, enum tuples become JSON
arrays, primitive-type formats propagate from the built-in primitive
definition, and generated schemas are checked with
`Draft202012Validator.check_schema()`.

SchemaCompiler validates schemas rather than user data instances. Runtime
instance validation belongs to ValidationEngine, which is implemented
separately. Lifecycle rules do not belong to SchemaCompiler.

## Consequences

Compilation stays deterministic, reusable for embedded schema fragments, and
cleanly separated from runtime value validation.

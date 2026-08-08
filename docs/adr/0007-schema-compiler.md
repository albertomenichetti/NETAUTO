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
constraint names are translated by SchemaCompiler, and enum tuples become JSON
arrays. SchemaCompiler is deterministic, does not mutate domain state, and
validates its generated schema with `Draft202012Validator.check_schema()`.
SchemaCompiler validates schemas rather than user data instances. Runtime
instance validation belongs to ValidationEngine in M1.1.5. Lifecycle rules do
not belong to SchemaCompiler.

## Consequences

Compilation stays small and reusable for embedded schema fragments, JSON
Schema concerns remain separated from the domain model, and validation of data
instances can evolve independently later.

# ADR 0009: Custom DataTypes

## Status

Accepted

## Context

NETAUTO needs an explicit domain-level way to create custom DataTypes while
keeping primitive types, schema compilation, and runtime validation as
separate concerns.

## Decision

A custom DataType has a stable UUID logical identity plus versioned schema
definitions. M1.1.6 creates `DataType` plus `DataTypeVersion` `v1` `DRAFT`
together. Custom DataTypes are based directly on built-in PrimitiveTypes, and
primitive names are resolved through the existing primitive registry. The
`core` namespace is reserved and cannot be used for custom DataTypes.
`core.string`, `core.integer`, `core.number`, and `core.boolean` remain
PrimitiveTypes rather than DataType resources. Constraints remain domain
Constraint objects and are validated by DataTypeVersion. SchemaCompiler and
ValidationEngine operate unchanged on factory-created versions. Custom-on-custom
datatype derivation is intentionally deferred. Global `namespace`/`name`
uniqueness is not the responsibility of the factory and requires
repository/application state. UUIDs are generated at custom DataType creation
time. Persistence is deferred to M1.1.8. Lifecycle and version operations
after initial `v1` `DRAFT` belong to M1.1.7.

## Consequences

Custom datatype creation stays small and domain-local, built-in primitives
remain distinct from versioned user types, and repository/persistence concerns
stay outside the factory.

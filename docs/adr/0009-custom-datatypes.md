# ADR 0009: Custom DataTypes

## Status

Accepted

## Context

NETAUTO needs an explicit domain-level way to create custom DataTypes while
keeping primitive types, schema compilation, and runtime validation as
separate concerns.

## Decision

A custom DataType has a stable UUID logical identity plus versioned schema
definitions. Creating a new custom DataType creates `DataType` plus
`DataTypeVersion v1 DRAFT`. Custom DataTypes are based directly on built-in
PrimitiveTypes, and primitive names are resolved through the primitive
registry. The `core` namespace is reserved and cannot be used for custom
DataTypes.

Built-in PrimitiveTypes remain:

- `core.string`
- `core.integer`
- `core.number`
- `core.boolean`
- `core.date`
- `core.datetime`
- `core.ip`
- `core.ip_prefix`

Constraints remain domain Constraint objects validated by DataTypeVersion.
SchemaCompiler and ValidationEngine operate unchanged on factory-created
versions. Custom-on-custom datatype derivation is intentionally not
implemented. Global `namespace`/`name` uniqueness is not the responsibility of
the factory and requires repository/application state. UUIDs are generated at
custom DataType creation time.

Current implementation status also includes:

- persisted custom DataTypes
- version lifecycle workflows
- REST API support
- CLI support
- repository/application uniqueness enforcement

## Consequences

Custom datatype creation stays small and domain-local, built-in primitives
remain distinct from versioned user types, and persistence and lifecycle
machinery stay outside the factory itself.

# ADR 0005: DataType Identity and Versioning

## Status

Accepted

## Context

NETAUTO distinguishes built-in primitive types from user-defined DataTypes,
while DataType schemas are versioned independently.

## Decision

DataType has a stable UUID identity. Its `namespace` and `name` form the
human-readable qualified name. Schema definitions are versioned separately
through `DataTypeVersion`. `DataTypeVersion` identity is the pair
`(datatype_id, integer version)` and does not have a separate UUID.
PrimitiveType and DataType are distinct concepts. Schema versions use
monotonically increasing positive integers rather than semantic versions.
Published version immutability is implemented now in both the
domain/application workflow and a defensive repository contract.

## Consequences

Human-readable names remain separate from stable identity, schema evolution
stays explicit, and built-in primitives are not conflated with versioned
user-defined DataTypes.

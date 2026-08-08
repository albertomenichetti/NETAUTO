# ADR 0006: DataType Constraints

## Status

Accepted

## Context

NETAUTO needs a small constraint vocabulary for `DataTypeVersion` without
exposing the full JSON Schema keyword surface in the domain model.

## Decision

Constraints are part of the NETAUTO domain language. The initial supported
constraints are `min_length`, `max_length`, `pattern`, `minimum`, `maximum`,
and `enum`. Constraint names use snake_case, and applicability depends on the
primitive base type. `enum` is a constraint, not a separate primitive type.
JSON Schema is a compiler target rather than the domain representation, and
keyword mapping belongs to the future SchemaCompiler. Nullability and defaults
are not DataType constraints. NETAUTO intentionally does not expose the
complete JSON Schema constraint vocabulary. Additional constraints should only
be introduced when concrete domain requirements justify them. `exclusive_minimum`,
`exclusive_maximum`, and `multiple_of` are intentionally deferred.

## Consequences

The domain stays small and explicit, compiler concerns remain separate, and
constraint growth is gated by actual modeling requirements.

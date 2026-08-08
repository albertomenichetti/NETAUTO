# ADR 0010: DataType Versioning

## Status

Accepted

## Context

NETAUTO needs explicit lifecycle and version-creation behavior for immutable
datatype schema snapshots while keeping compiler and validation behavior
independent from lifecycle policy.

## Decision

DataTypeVersion is an immutable value object. `(datatype_id, version)` remains
version identity. Draft revision produces a replacement snapshot with the same
identity. Lifecycle is `DRAFT -> PUBLISHED -> DEPRECATED`, and `DEPRECATED` is
terminal. Publishing validates compilability through SchemaCompiler. Published
schema definitions are never modified; schema changes after publication require
a new version. New versions are created from a PUBLISHED source. Version
numbers are monotonic and use `max(existing)+1`. The source version determines
the cloned schema, while the existing set determines the next number.
Publishing a new version does not automatically deprecate old versions, and
multiple PUBLISHED versions may coexist. "Latest published" selection belongs
to future repository/application logic. Compiler and validator remain
lifecycle-independent. Persistence is intentionally deferred to M1.1.8.
Custom DataType inheritance remains deferred.

## Consequences

Lifecycle changes become explicit, published schemas remain stable, and later
repository logic can manage current-version selection without changing the core
versioning semantics.

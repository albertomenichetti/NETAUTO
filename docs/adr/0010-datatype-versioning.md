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
a new version. New versions are created from a PUBLISHED or DEPRECATED source.
Version numbers are monotonic and use `max(existing)+1`. The source version
determines the cloned schema, while the existing set determines the next
number. Publishing a new version does not automatically deprecate old
versions, and multiple PUBLISHED versions may coexist. "Latest published"
selection belongs to future repository/application logic. Compiler and
validator remain lifecycle-independent.

Persistence hardening implemented in S4a adds a repository-level defensive
boundary beneath the application/domain workflow:

- new persisted versions must enter as DRAFT
- DRAFT -> DRAFT may revise constraints only
- DRAFT -> PUBLISHED is status-only
- PUBLISHED -> DEPRECATED is status-only
- DEPRECATED is terminal in repository replacement rules
- base_type is stable across the full DataType lineage

These are repository API guarantees, not declarative SQL lifecycle triggers.
Arbitrary raw SQL may still corrupt lifecycle or base_type state; detecting
that remains future integrity-verifier work. Custom DataType inheritance
remains deferred.

## Consequences

Lifecycle changes remain explicit, published schemas remain stable, and the
repository now prevents direct persistence-layer snapshot rewrites that bypass
supported DataTypeVersion workflows without moving lifecycle semantics into SQL.

# ADR 0003: Schema Versioning

## Status

Accepted

## Context

Both DataType and ObjectTemplate are versioned and move through an explicit
lifecycle.

## Decision

Use the lifecycle `draft -> published -> deprecated`, keep published versions
immutable, and require references from published schemas to point to exact
versions.

Repository-level persistence hardening now enforces the lifecycle contract for
exact version snapshots:

- new persisted versions enter as `draft`
- publication is a status-only transition
- deprecation is a status-only transition
- `deprecated` is terminal

Implemented slices:

- `DataTypeVersion` persistence enforcement in S4a
- `ObjectTemplateVersion` persistence enforcement in S4b

This is repository-level enforcement. It does not imply SQL lifecycle triggers
or make arbitrary raw SQL lifecycle rewrites impossible.

## Consequences

Published schemas are stable and reproducible, and downstream references do
not drift to newer definitions implicitly. Supported application workflows
remain the primary semantic authority, while repositories provide a second
preventive boundary against illegal persisted snapshot rewrites.

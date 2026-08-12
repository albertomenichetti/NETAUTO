# ADR 0003: Schema Versioning

## Status

Accepted

## Context

Both DataType and ObjectTemplate are versioned and move through an explicit
lifecycle.

## Decision

Use the lifecycle `draft -> published -> deprecated`, keep published versions
immutable, and require references from published schemas to point to exact
versions where the current model is designed around exact-version pinning.

Current implemented reference split:

- exact version references:
  - `ObjectTemplateVersion.parent`
  - `ObjectTemplateProperty -> DataTypeVersion`
  - `Object -> ObjectTemplateVersion`
- stable identity references:
  - `ObjectTemplateComponent -> ObjectTemplate`
  - `RelationshipDefinition` endpoint templates

Repository-level persistence hardening also enforces the lifecycle contract for
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

Published schemas are stable and reproducible. Exact-version references do not
drift implicitly, while the few deliberately stable-identity references remain
explicit architectural choices rather than accidental omissions.

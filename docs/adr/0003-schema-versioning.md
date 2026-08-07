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

## Consequences

Published schemas are stable and reproducible, and downstream references do
not drift to newer definitions implicitly.

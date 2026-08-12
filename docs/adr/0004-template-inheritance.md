# ADR 0004: Template Inheritance

## Status

Accepted

## Context

ObjectTemplate inheritance rules are fixed by the architecture contract.

## Decision

Use single inheritance with an exact pinned parent version.

Current implemented rules:

- published versions are immutable
- same-template inheritance is forbidden
- inheritance cycles are not allowed
- inherited property names cannot be shadowed locally
- inherited component names cannot be shadowed locally
- inherited properties cannot be removed or changed to a different datatype
- abstract templates cannot be instantiated
- stable parent identity and monotonic exact parent-version evolution are
  defined further in ADR 0015

Component-slot compatibility and RelationshipDefinition applicability both
reuse exact pinned ancestry resolution.

## Consequences

Template evolution stays predictable, and child templates remain semantically
compatible with their ancestor templates without introducing a second ancestry
model.

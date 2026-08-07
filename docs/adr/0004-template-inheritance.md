# ADR 0004: Template Inheritance

## Status

Accepted

## Context

ObjectTemplate inheritance rules are fixed by the architecture contract.

## Decision

Use single inheritance with pinned parent versions. Published versions are
immutable. Inheritance cycles are not allowed. Inherited properties cannot be
removed or changed to a different datatype. Abstract templates cannot be
instantiated.

## Consequences

Template evolution stays predictable, and instances of child templates remain
semantically compatible with their ancestor templates.

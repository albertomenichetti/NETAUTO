# ADR 0002: JSON Schema for Dynamic Types

## Status

Accepted

## Context

NETAUTO supports dynamic user-defined types, while Pydantic is reserved for
static API models.

## Decision

Represent dynamic DataTypes as JSON Schema Draft 2020-12 and validate them
with `jsonschema` rather than generating Pydantic models dynamically.

## Consequences

Static API contracts stay separate from dynamic domain schemas, and validation
remains strict without implicit coercion.

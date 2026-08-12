# ADR 0017: Relational Structural Metadata

## Status

Accepted

## Context

NETAUTO persists several categories of information:

- current authoritative structural model metadata
- runtime dynamic values
- historical snapshots

These categories do not have the same relational integrity needs.

When a persisted structure contains authoritative references to another current
model entity, the database should enforce that reference directly where the
shape is representable as relational columns and foreign keys. JSON remains
useful for dynamic runtime values and historical snapshots, where relational
normalization is either not representationally appropriate or not the current
goal.

During this development phase the SQLite database is intentionally recreated
from scratch after schema changes. In-place migration and backfill are not yet
part of the project.

Historical note: the fresh-database and no-Alembic assumptions below reflect
the original phase decision. They are now superseded as a long-term direction
by ADR 0021, which moves Alembic and PostgreSQL ahead of dogfooding. Current
code still uses the fresh-SQLite workflow today.

## Decision

General rule:

- current authoritative structural reference -> relational column/table plus
  physical foreign key where representable
- runtime dynamic value -> JSON may be appropriate
- historical snapshot -> JSON may be appropriate

Current application of that rule:

- ObjectTemplate property declarations -> relational child table with exact
  owner and exact DataTypeVersion FK
- ObjectTemplate component declarations -> relational child table with exact
  owner and stable target ObjectTemplate FK
- ObjectTemplate parent references -> relational exact-version columns plus
  composite FK
- Object exact template pins -> relational exact-version columns plus
  composite FK
- Runtime ComponentMembership edges -> relational current structural edge
- RelationshipDefinition endpoints -> relational stable-template FKs
- runtime Relationship definition and endpoint references -> relational FKs
  plus ordered uniqueness
- Object properties -> remain JSON as runtime dynamic values
- ObjectChange before/after snapshots -> remain JSON as historical snapshots
- ObjectChange `object_id` -> stored without a destructive FK so history
  survives Object deletion
- DataTypeVersion constraints -> remain JSON as embedded constraint values, not
  structural foreign references

This phase uses a fresh-database contract:

- no in-place migration or backfill of existing databases
- no Alembic in this phase
- no dual reads of legacy representations
- no dual writes to old and new representations

Supersession note:

- this remains a correct description of the current implementation phase
- it is no longer the accepted long-term workflow
- Alembic becomes the authoritative schema-evolution mechanism in M2.5.4
- PostgreSQL becomes the authoritative SQL backend per ADR 0021

## Consequences

- SQLite can physically reject an ObjectTemplate property that references a
  nonexistent exact DataTypeVersion
- SQLite can physically reject an ObjectTemplate component declaration that
  references a nonexistent target ObjectTemplate identity
- SQLite can physically reject an Object that references a nonexistent exact
  ObjectTemplateVersion
- SQLite can physically reject a RelationshipDefinition that references a
  nonexistent ObjectTemplate endpoint identity
- SQLite can physically reject a runtime Relationship that references a
  nonexistent definition or nonexistent Object endpoint
- SQLite can physically reject duplicate ordered runtime Relationship triples
- runtime Object history survives Object deletion because ObjectChange is not
  tied to a destructive runtime Object FK
- repository and test fixtures must create real referenced rows rather than
  arbitrary UUID text where structural references exist
- dogfood databases are recreated rather than migrated during this development
  stage

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

## Decision

General rule:

- current authoritative structural reference -> relational column/table plus
  physical foreign key where representable
- runtime dynamic value -> JSON may be appropriate
- historical snapshot -> JSON may be appropriate

Applied in this phase:

- ObjectTemplate property declarations -> relational, implemented in S3a
- ObjectTemplate component declarations -> relational, implemented in S3b
- Object properties -> remain JSON as runtime dynamic values
- ObjectChange before/after snapshots -> remain JSON as historical snapshots
- DataTypeVersion constraints -> remain JSON as embedded constraint values, not
  structural foreign references

This phase uses a fresh-database contract:

- no in-place migration or backfill of existing databases
- no Alembic in this slice
- no dual reads of legacy representations
- no dual writes to old and new representations

After S3b there is exactly one authoritative SQL persistence representation for
ObjectTemplate structural declarations:

- properties -> relational child table
- components -> relational child table

## Consequences

- SQLite can physically reject an ObjectTemplate property that references a
  nonexistent exact DataTypeVersion.
- SQLite can physically reject an ObjectTemplate component declaration that
  references a nonexistent target ObjectTemplate identity.
- Whole-owner deletion of an exact ObjectTemplateVersion can cascade cleanly to
  owned property rows and component rows.
- Repository and test fixtures must create real referenced DataTypeVersion
  rows and real referenced ObjectTemplate identity rows rather than relying on
  arbitrary UUID text in JSON.
- Existing dogfood databases are recreated rather than migrated during this
  development stage.

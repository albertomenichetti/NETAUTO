# ADR 0011: DataType Persistence

## Status

Accepted

## Context

NETAUTO needs durable storage for the DataType slice while preserving the
domain core boundary.

## Decision

The DataType slice is persisted through SQLAlchemy-backed repositories behind
persistence-neutral contracts. Domain objects remain separate from ORM row
models, and core repository contracts contain no SQLAlchemy dependency.
SQLite is the initial implemented SQL backend; PostgreSQL remains a later
target.

Current persistence decisions:

- DataType UUID is stored canonically as text in SQLite
- `(namespace, name)` is repository/database unique
- `(datatype_id, version)` is the DataTypeVersion persistence identity
- PrimitiveTypes are not persisted; the base primitive is stored by canonical
  primitive name
- constraints are persisted as deterministic JSON TEXT
- JSON TEXT is intentional so Python integer precision is not narrowed by
  SQLite numeric storage
- enum arrays round-trip back into immutable domain tuples
- loaded rows are reconstructed through real domain constructors and are
  therefore revalidated

Lifecycle workflow semantics remain in the domain/application layer, and the
persistence-neutral repository contract now also adds defensive lifecycle and
base-type enforcement beneath those workflows. `replace_version` persists
immutable replacement snapshots subject to those repository checks. UnitOfWork
owns commit and rollback boundaries.

Current implementation status:

- the production composition root creates the SQLite engine and calls
  `create_schema(engine)`
- SQLite is the only implemented SQL backend
- Alembic is not implemented
- REST and CLI behavior are implemented elsewhere in the stack
- raw SQL can still bypass semantic lifecycle rules

## Consequences

Persistence establishes a reusable adapter pattern while keeping domain
semantics, integer precision, transaction intent, and repository defensive
immutability rules explicit.

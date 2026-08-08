# ADR 0011: DataType Persistence

## Status

Accepted

## Context

NETAUTO needs durable storage for the DataType slice while preserving the
domain core boundary and keeping lifecycle logic outside persistence code.

## Decision

M1.1.8 persists the DataType slice. Domain objects remain separate from ORM
row models, and core repository contracts contain no SQLAlchemy dependency.
SQLite is the initial reference backend; PostgreSQL remains a later target.
DataType UUID is stored canonically as text in SQLite. `(namespace, name)` is
repository/database unique. `(datatype_id, version)` is the DataTypeVersion
persistence identity. PrimitiveTypes are not persisted; the base primitive is
stored by canonical primitive name. Constraints are persisted as deterministic
JSON TEXT. JSON TEXT is intentional so Python integer precision is not narrowed
by SQLite numeric storage. Enum arrays round-trip back into immutable domain
tuples. Loaded rows are reconstructed through real domain constructors and are
therefore revalidated. Lifecycle logic remains in DataTypeVersioningService,
not repository code. `replace_version` persists immutable replacement
snapshots. UnitOfWork owns commit and rollback boundaries. There is no
import-time database creation, no Alembic yet, and no REST or CLI behavior in
this milestone.

## Consequences

Persistence establishes a reusable adapter pattern for later model slices while
keeping domain semantics, integer precision, and transaction intent explicit.

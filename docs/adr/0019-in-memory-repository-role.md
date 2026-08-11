# ADR 0019: In-Memory Repository Role

## Status

Accepted

## Context

NETAUTO maintains both in-memory and SQLAlchemy repository implementations.
They serve different purposes.

The in-memory backend is used heavily in repository-contract, application, API,
and CLI tests because it is fast and persistence-neutral. At the same time,
the SQLAlchemy backend is the real relational persistence implementation and is
responsible for physical foreign keys, relational child tables, transaction
boundaries, locking behavior, and raw-storage interaction.

Confusion between these roles causes two problems:

- semantic repository rules may be enforced only in SQL while memory becomes an
  invalid fixture backdoor
- tests may incorrectly expect the in-memory backend to emulate database
  behavior that belongs only to SQL/backend-specific integration tests

## Decision

In-memory repositories are reference implementations of persistence-neutral
repository semantics used for fast semantic/application testing.

They are not database emulators.

They must enforce repository-contract behavior shared by all backends,
including for example:

- lifecycle permissions
- duplicate and not-found semantics
- deterministic ordering
- snapshot immutability
- repository-level ownership/cardinality rules

They must not attempt to emulate backend-specific persistence behavior,
including for example:

- foreign-key enforcement details
- `ON DELETE CASCADE` / `RESTRICT` mechanics
- SQL `CHECK` constraints
- indexes
- autoflush behavior
- transaction isolation
- SQLite writer locking
- SQL statement ordering
- raw SQL corruption behavior

Testing split:

- shared repository-contract and semantic tests -> memory + SQL backend
- physical relational/backend tests -> SQL/backend-specific test suites only

If a lifecycle or immutability rule belongs to the repository contract, tests
must obey it in memory too. The in-memory backend is not an allowed fixture
bypass for repository-forbidden states.

## Consequences

- Repository semantics are exercised consistently across memory and SQLAlchemy.
- Application and API tests cannot seed impossible repository states through
  the in-memory backend.
- SQL/backend-specific tests remain the place for FK, transaction, locking,
  and statement-shape assertions.

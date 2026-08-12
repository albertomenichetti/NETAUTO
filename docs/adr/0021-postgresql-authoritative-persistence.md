# ADR 0021: PostgreSQL Authoritative Persistence

## Status

Accepted

## Context

SQLite is currently the only implemented SQL backend in the repository.

The project previously retained SQLite through model hardening, dogfooding,
freeze, verifier, and destructive certification, with PostgreSQL and Alembic
deferred to a later backend milestone.

Recent cross-plane concurrency analysis invalidated that sequencing
assumption.

The project has now identified transactional invariants that require real
concurrent transactional primitives to be designed, implemented, and verified
during model hardening rather than postponed until a late backend port.

Examples include, but are not limited to:

- creating an Object pinned to an exact `ObjectTemplateVersion` while that
  version is concurrently deprecated
- choosing the highest `PUBLISHED` `ObjectTemplateVersion` while model-plane
  lifecycle changes occur concurrently
- migrating Objects to a target `ObjectTemplateVersion` while that target is
  concurrently invalidated for new bindings
- creating runtime bindings while their referenced model-plane identities are
  concurrently deleted
- coordinating model-plane decision reads with new data-plane bindings

SQLite's physical single-writer behavior can serialize interactions that the
intended architecture treats as logically independent. That can hide races
rather than characterize them faithfully.

Designing PostgreSQL semantics speculatively and postponing executable
verification would accumulate unacceptable technical debt.

## Decision

- PostgreSQL becomes the authoritative and only intended supported SQL
  backend.
- SQLite is deprecated and scheduled for complete removal.
- NETAUTO does not commit to long-term SQLite/PostgreSQL behavioral parity.
- In-memory repositories remain test doubles/reference infrastructure as
  currently defined; they are not promoted to production persistence.
- Alembic becomes the authoritative PostgreSQL schema-evolution mechanism.
- PostgreSQL and Alembic move before M3 dogfooding.
- M3 is blocked until M2.5 PostgreSQL Transactional Foundation closes.

## Transactional Rationale

The project now requires a backend whose real transactional behavior can be
used to characterize and certify concurrency semantics directly rather than
inferred from a backend with materially different write behavior.

Relevant PostgreSQL capabilities to be explored and used later include:

- MVCC
- transaction-scoped advisory locks
- row-level locking
- multiple lock compatibility modes
- real concurrent writers
- transaction isolation and `SERIALIZABLE` where justified
- deadlock detection
- transactional FK and constraint behavior

This ADR does not declare the final primitive for any specific logical guard
or binding protocol. It records that those questions must now be solved and
verified against PostgreSQL rather than deferred.

## Consequences

- PostgreSQL migration becomes immediate project work.
- SQLite compatibility is no longer a design constraint for new concurrency
  semantics.
- SQLite-specific code remains temporarily only as transition code until its
  dedicated removal milestone.
- new concurrency invariants can be tested using real PostgreSQL transactions
  rather than inferred from SQLite behavior.
- dogfooding starts only after the transactional foundation is real.
- schema evolution during dogfooding will proceed through Alembic rather than
  fresh-database recreation as the long-term development workflow.

## Non-Decisions

This ADR does not yet decide:

- the exact cross-plane model-binding protocol
- whether individual invariants beyond the two implemented logical guards use
  row locks, advisory locks, `SERIALIZABLE`, or a combination
- final lock ordering for later cross-plane protocols
- retry policy for PostgreSQL serialization or deadlock failures
- final transaction isolation level for all workflows

Those decisions belong to later narrowly scoped M2.5 milestones.

## Subsequent Resolution Note

After acceptance of this ADR, M2.5.8 resolved the PostgreSQL realization of
`MODEL_PLANE_GUARD` to an exclusive transaction-level advisory lock using
`pg_try_advisory_xact_lock(...)`.

M2.5.9 now resolves the PostgreSQL realization of
`OWNERSHIP_GRAPH_GUARD` to a distinct exclusive transaction-level advisory
lock using `pg_try_advisory_xact_lock(...)`.

The two implemented guard domains now use distinct advisory keys within the
same stable NETAUTO advisory namespace:

- key `1` -> `MODEL_PLANE_GUARD`
- key `2` -> `OWNERSHIP_GRAPH_GUARD`

M2.5.12 subsequently removed:

- SQLite runtime/backend selection support
- SQLite-specific writer unit-of-work implementations and retry paths
- SQLite-backed test authority and legacy compatibility coverage

PostgreSQL is now the sole supported SQL backend.

Still unresolved after M2.5.12:

- cross-plane binding protocols
- later invariant-specific lock ordering and retry policy

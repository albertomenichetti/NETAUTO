# ADR 0016: Model-Plane Writer Serialization

## Status

Accepted

## Context

NETAUTO separates a model plane from a data plane.

Model plane:

- DataType / DataTypeVersion
- ObjectTemplate / ObjectTemplateVersion
- RelationshipDefinition

Data plane:

- Object
- ComponentMembership
- runtime Relationship
- ObjectChange

Model-plane mutations are rare administrative operations, but many of their
invariants require global `check -> mutate` reasoning over shared schema state.
Running those mutations concurrently risks making decisions from snapshots that
are stale before mutation starts.

## Decision

All model-plane mutations use a dedicated global model-write unit of work.

Model read:

- normal unit of work

Model write:

- global model-write unit of work
- acquire serialization before the first decision read
- validate
- mutate
- commit or rollback
- release serialization

Data read/write:

- normal unit of work

For the current SQLite backend, the model-write unit of work acquires the
writer reservation with `BEGIN IMMEDIATE` at unit-of-work entry. The
reservation is transaction-scoped and remains active until commit or rollback.
If another writer already holds SQLite's writer slot, acquisition may wait and
retry a bounded number of times before the model operation begins.

The persistence-neutral application contract is the logical model-plane writer
serialization, not SQLite's `BEGIN IMMEDIATE` itself. A future PostgreSQL
backend may satisfy the same contract using another database-backed mechanism,
such as a transaction-scoped advisory lock.

## Consequences

Supported model-plane mutations cannot concurrently execute their
`check -> mutate` critical sections on SQLite.

Model-plane REST APIs remain synchronous request/response operations. NETAUTO
does not introduce asynchronous queues, background workers, durable command
storage, or command replay for model mutations in this phase.

On SQLite, bounded acquisition retry applies only to writer reservation
acquisition at `BEGIN IMMEDIATE`, before repositories are initialized and
before the first decision read. The application command itself is not retried,
semantic validation is not replayed, and commit is not retried.

Retryable contention is classified from the DBAPI SQLite error code as
`SQLITE_BUSY`. If bounded acquisition is exhausted, the persistence layer
surfaces a persistence-neutral temporary-unavailability signal that REST maps
to HTTP 503 with `Retry-After`.

Model-plane reads remain ordinary concurrent reads. Data-plane operations
continue using the ordinary unit of work and do not explicitly acquire the
logical model-plane lock through the application architecture.

This ADR does not claim that every future data-plane concurrency problem is
solved across all backends. Subsequent runtime concurrency characterization and
remediation are now governed by ADR 0020, which introduces
`OWNERSHIP_GRAPH_GUARD` as a distinct logical coordination domain from
`MODEL_PLANE_GUARD`.

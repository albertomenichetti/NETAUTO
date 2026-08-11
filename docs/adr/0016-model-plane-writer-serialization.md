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

The persistence-neutral application contract is the logical model-plane writer
serialization, not SQLite's `BEGIN IMMEDIATE` itself. A future PostgreSQL
backend may satisfy the same contract using another database-backed mechanism,
such as a transaction-scoped advisory lock.

## Consequences

Supported model-plane mutations cannot concurrently execute their
`check -> mutate` critical sections on SQLite.

Model-plane reads remain ordinary concurrent reads. Data-plane operations
continue using the ordinary unit of work and do not explicitly acquire the
logical model-plane lock through the application architecture.

On SQLite, a held model-write transaction also occupies SQLite's single writer
slot, so another write transaction cannot complete through a separate
connection while the model transaction is active. This is acceptable and
desirable for the current backend because it also closes model-vs-data
check/mutate races before the later strong-FK milestones.

This ADR does not claim that every future data-plane concurrency problem is
solved across all backends. Composition graph mutations and other data-plane
paths may require later dedicated concurrency analysis.

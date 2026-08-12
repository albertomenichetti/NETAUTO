# ADR 0020: Runtime Concurrency Control Domains

## Status

Accepted

## Context

NETAUTO has multiple concurrency-sensitive mutation domains with materially
different invariants:

- model-plane schema/version mutations
- ownership-topology mutations
- Object content/state mutations
- ordinary runtime data operations

The architecture must not collapse these into one global database-writer lock.
SQLite is currently the only supported backend and is physically restrictive,
but those backend limits must not redefine the long-term semantic contract for
future PostgreSQL support.

## Decision

Concurrency protection is semantic, not database-global.

Logical coordination domains:

- `MODEL_PLANE_GUARD`
  Covers `DataType`, `ObjectTemplate`, and `RelationshipDefinition` mutations.
- `OWNERSHIP_GRAPH_GUARD`
  Covers `attach_component`, `detach_component`, and `delete_object` /
  subtree-delete workflows.
- Object content/state writes
  Use optimistic conditional replacement.
- Ordinary data operations
  Continue using ordinary relational concurrency and structural constraints.

The runtime architecture is therefore:

- model plane
  `MODEL_PLANE_GUARD`
- ownership topology
  `OWNERSHIP_GRAPH_GUARD`
- Object content
  optimistic conditional writes
- runtime Relationship writes, Object creation, reads, history reads
  no logical global guard

### MODEL_PLANE_GUARD

ADR 0016 defines model-plane writer serialization. That serialization is a
logical coordination domain, not a mandate to lock the whole database.

SQLite currently realizes this using `BEGIN IMMEDIATE` because of SQLite's
backend constraints.

A future PostgreSQL backend must provide an equivalent transaction-scoped
logical model-plane guard using a PostgreSQL-appropriate primitive such as:

- advisory transaction locking
- transactional row locking on a dedicated guard row

The semantic requirement is:

- acquire model-plane serialization before the first decision read
- do not replay the application command automatically
- do not globally block unrelated ordinary data-plane writes merely because the
  database supports concurrent writers

### OWNERSHIP_GRAPH_GUARD

`attach_component`, `detach_component`, and `delete_object` / subtree delete
make decisions from the current ownership topology and then mutate that
topology.

These workflows require a second logical coordination domain:

- read graph
- validate
- mutate graph

against a stable ownership topology.

`OWNERSHIP_GRAPH_GUARD` is distinct from `MODEL_PLANE_GUARD`.

Therefore a future PostgreSQL backend must be able to represent, conceptually:

- Tx A holds `MODEL_PLANE_GUARD`
- Tx B holds `OWNERSHIP_GRAPH_GUARD`

at the same time.

`OWNERSHIP_GRAPH_GUARD` is now implemented for:

- `attach_component`
- `detach_component`
- `delete_object` / subtree delete

SQLite currently realizes this guard using `BEGIN IMMEDIATE` before the first
decision read in the structural transaction.

SQLite acquisition semantics are:

- bounded `SQLITE_BUSY` retry on guard acquisition only
- no application command replay
- no commit retry

If acquisition is exhausted, the backend raises
`OwnershipGraphWriteUnavailable`, which REST maps to HTTP `503 Service
Unavailable`.

Application composition is fail-closed:

- `ObjectApplicationService` requires an explicit
  `OWNERSHIP_GRAPH_GUARD` UoW factory
- `create_app(...)` requires an explicit ownership-graph UoW factory
- there is no fallback from structural mutations to the ordinary runtime UoW

Although `MODEL_PLANE_GUARD` and `OWNERSHIP_GRAPH_GUARD` are distinct logical
domains, SQLite currently maps both onto the same single-writer reservation.
That physical contention is a SQLite backend limitation, not the intended
cross-backend architecture.

### Object content/state mutation

Ordinary Object content uses optimistic concurrency:

- read snapshot `S`
- build candidate `S'`
- conditionally replace only if the persisted current snapshot still equals `S`

If the stored Object has changed since `S` was read, the write fails with a
concurrency conflict.

The application command is not retried automatically.

### Future PostgreSQL contract

The future PostgreSQL architecture must preserve these semantics:

- `MODEL_PLANE_GUARD`
  independent logical transaction guard
- `OWNERSHIP_GRAPH_GUARD`
  independent logical transaction guard
- Object property/content writes
  optimistic concurrency
- runtime Relationship writes
  ordinary relational concurrency plus constraints
- no global PostgreSQL database writer lock

Consequently:

- a model-plane mutation and an Object property update remain logically
  concurrent
- an ownership attach and an unrelated Object property update remain logically
  concurrent
- a future PostgreSQL backend must be able to acquire `MODEL_PLANE_GUARD` and
  `OWNERSHIP_GRAPH_GUARD` independently, for example with separate advisory
  lock keys or separate transactional guard rows
- a future PostgreSQL implementation must not solve runtime concurrency by
  introducing one global database writer lock

### Cross-domain caveat

`OWNERSHIP_GRAPH_GUARD` coordinates supported structural mutations against each
other.

It does not by itself prove every cross-domain interaction safe on future
PostgreSQL backends.

In particular, the following remain explicitly uncharacterized for future
concurrency review:

- `delete_object` vs concurrent Object property update
- `delete_object` vs concurrent Object migration

These interactions cross the ownership-topology and Object-content domains and
must not be claimed solved merely because SQLite currently uses one physical
writer reservation.

## Consequences

NETAUTO does not serialize all runtime writes behind one global coordination
mechanism.

Different invariants are protected by different strategies:

- model-plane serialization
- ownership-topology serialization
- Object optimistic concurrency
- ordinary relational constraints

This allows targeted concurrency hardening without redefining the overall
architecture around one database-global writer lock.

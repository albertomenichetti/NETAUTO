# M4 WIP — Top-down API closure sweep

Status: WIP / NON-NORMATIVE

## Purpose

The first M4 discovery pass was bottom-up: start from the current relational/domain model, inspect operation implementations, identify unnecessary reads, cacheable immutable knowledge, denormalization/materialization opportunities, and candidate simplifications.

The next pass intentionally reverses direction. It starts from the external caller and public API contract, then drives downward into application data paths, persistence, cache, relational structures, and concurrency guarantees.

The goal of this sweep is to reach a complete TO-BE closure for the data plane before performing the final global concurrency/schema design phase.

## Scope order

Review the most important data-plane constructs first:

1. Object
2. factual Relationship
3. Lifecycle

Model-plane APIs remain available as supporting dependencies, but this sweep prioritizes the runtime caller experience and the cost/safety of the hot data-plane paths.

## Per-operation closure checklist

For every public operation, review and freeze in this order:

### 1. Public signature

Freeze:

- HTTP method;
- route;
- path parameters;
- query parameters;
- request semantics;
- success status;
- error semantics that are part of the public contract.

Do not let the existing route shape remain merely because it mirrors current persistence or historical implementation convenience.

### 2. Request and response JSON model

Freeze the exact public wire model from the caller perspective.

As soon as one operation's request/response model is agreed, persist it explicitly in M4 documentation rather than leaving it implicit in conversation or Python DTOs.

Collections and specific-resource reads must be evaluated independently. In particular, a list item should not automatically reuse the full detail DTO when some fields are unbounded or expensive.

#### Mutation response vs current-resource representation

Mutation response semantics must be reviewed independently from the richness of the corresponding current-resource GET projection.

Canonical review direction:

```text
legal mutation work
    -> operation-owned result that the caller actually needs
    -> minimal successful response capable of communicating that result
```

The reverse coupling is not a valid default:

```text
rich GET projection
    -> mutation must reconstruct the same projection after success
```

A mutation must not incur additional backend reads, model reconstruction, component/relationship expansion or other response-only work solely because a GET DTO is richer than the command acknowledgement requires.

For a mutation of an existing resource, the default candidate is therefore:

```text
successful mutation
+ no operation-owned result value required by the caller
    -> 204 No Content
```

For creation, review whether the canonical resource URI completely communicates the server-allocated identity:

```text
Location fully identifies the created resource
    -> 201 Created
    -> Location
    -> no duplicated complete-resource body by default

operation allocates an additional caller-required value
not naturally communicated by Location
    -> return only the minimal generated carrier needed by that operation
```

These are **review defaults, not blanket cross-family freezes**. Every route must still ratify its exact success status/body during its own family sweep. A concrete operation may return data when that data is genuinely part of its operation-owned result or a demonstrated caller need justifies it; it must not return a complete resource representation merely for uniformity or convenience.

Once a family owner has ratified the concrete response contract, that family owner is authoritative for the route. Git history remains the evidence for superseded mutation-response brainstorming.

### 3. Data structures touched

Record the exact current and TO-BE data structures required by the operation:

- authoritative mutable tables;
- immutable/materialized model tables;
- derived runtime tables;
- lifecycle tables;
- worker-local caches;
- any proposed new relational structure.

Distinguish between structures required for current admission/state and structures required only for immutable semantic interpretation.

### 4. Current cost

Record how expensive the operation is today in concrete terms:

- SQL statement count;
- recursive/model traversals;
- number of rows or unbounded payloads read;
- application-side recertification;
- N+1 patterns;
- data copied only to build a response body;
- unnecessary JSONB transfer/decoding;
- work performed inside the Unit of Work that could be outside it.

### 5. TO-BE cost and denormalization check

Identify the heaviest operations and verify whether the bottom-up denormalization/materialization candidates already solve the problem.

Examples already discovered include:

- stable ObjectTemplate lineage closure;
- immutable ObjectTemplate effective schema materialization;
- enriched `object_components` semantic edge identity;
- persisted complete factual Relationship runtime-resolution closure;
- immutable exact schema caches for ObjectTemplate / DataType / RelationshipDefinitionVersion.

For every heavy operation, explicitly classify:

- already solved by an agreed candidate;
- partially solved;
- unresolved and likely requiring additional relational/schema change.

### 6. Concurrency guarantees required

Describe the semantic outcome the concurrency model must guarantee from the caller perspective, without prematurely selecting row locks.

Examples:

- exactly one current owner for an Object child;
- no ownership cycle;
- Object schema-change cannot leave outgoing components invalid;
- factual Relationship exact views have one current owner;
- mutation events correspond atomically to the committed factual transition;
- deletes cannot race through current blockers;
- model mutations cannot make a newly admitted runtime fact invalid at commit.

This sweep records the required guarantees. The subsequent global phase will derive the concrete lock/FK/arbitration protocol from the complete set of guarantees.

### 7. Cache use

For each operation record:

- whether cache can help;
- exact cache key/value;
- whether the cached knowledge is immutable/stable enough for worker-local caching without coherence protocol;
- hot-cache behavior;
- cold-cache behavior;
- exact data source used to fill the cache;
- whether filling adds a new SQL statement or opportunistically consumes an already required payload;
- whether lifecycle changes require invalidation.

A cache entry must never be used as proof of current mutable existence/admissibility.

### 8. Relational-schema implications

At the end of each operation, record any schema implication as one of:

- none;
- already-covered candidate;
- new candidate to carry into the final schema phase;
- unresolved question.

Do not implement schema changes during this discovery sweep.

## Freeze discipline

The sweep is intentionally caller-first and incremental.

For each operation:

1. discuss the public signature;
2. agree it;
3. persist the frozen candidate explicitly;
4. discuss and agree the request/response wire model;
5. persist it explicitly;
6. continue downward through data path, cost, denormalization, concurrency guarantees, cache, and schema implications.

The word "freeze" in this WIP means design closure for the M4 TO-BE candidate; normative milestone contract/architecture files remain subject to the normal M4 governance gates.

## Expected output of the sweep

At completion, M4 should have a caller-oriented TO-BE specification for Object, factual Relationship and Lifecycle with closure across:

```text
public API
-> exact JSON wire contract
-> application semantics
-> authoritative/derived data structures
-> expected hot/cold data path
-> current vs target cost
-> denormalization/materialization dependencies
-> concurrency guarantees
-> cache behavior and fill policy
-> explicit relational-schema implications
```

The following phase can then work globally rather than operation-by-operation:

```text
frozen TO-BE API/data paths
-> semantic concurrency matrix
-> safety predicates
-> concrete PostgreSQL arbitration / lock / FK design
-> final relational schema changes
-> deterministic concurrency verification
```

## Starting point

Begin with Object because it is the central data-plane aggregate and touches:

- exact ObjectTemplate runtime schema;
- properties;
- ownership/components;
- schema evolution;
- factual Relationship blockers;
- lifecycle history.

Review Object operations one at a time from the caller perspective before moving to factual Relationship and then Lifecycle.

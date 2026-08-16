# Concurrency and Unit of Work — Current AS-IS

## Purpose and authority

Concurrency is part of semantic correctness. A domain invariant is not considered guaranteed if a supported legal interleaving can violate it.

The architecture separates:

```text
semantic safety predicate
    -> required guarantee
    -> persistence / transaction authority
    -> PostgreSQL realization
    -> deterministic real-PostgreSQL verification
```

Authority is divided deliberately:

```text
concurrency-matrix.md
    -> canonical mutation census
    -> semantic interaction scopes
    -> safety-predicate definitions
    -> allowed outcomes

this document
    -> Unit of Work boundaries
    -> isolation, locks, gates and constraint realization
    -> retry / convergence realization

verification-concurrency-registry.md
    -> stable deterministic scenarios and recipes
```

The semantic guarantee is authoritative; PostgreSQL mechanisms realize it and must not silently redefine it. This document therefore uses predicate IDs defined in `concurrency-matrix.md` without duplicating their normative catalog.

## Semantic Unit of Work

One semantic kernel mutation is one PostgreSQL write Unit of Work.

A mutation UoW includes, as applicable:

1. state-dependent admission reads;
2. default/dependency resolution;
3. candidate derivation and canonical validation;
4. stabilization/locking of relevant predicates;
5. required current-state writes;
6. complete required lifecycle-event set;
7. atomic commit or rollback.

Repository/DAO operations do not own independent commits. The transaction boundary belongs to the application semantic command/UoW.

Pure syntactic parsing/validation that does not depend on mutable persisted state may occur before opening the transaction. Any correctness predicate dependent on current state must be evaluated and stabilized inside the UoW.

Failure rolls back the entire semantic UoW. When a race requires retry or convergence, the retry normally restarts the **entire semantic UoW** from fresh state rather than retrying an internal repository fragment with stale assumptions.

## Isolation baseline

Mutation baseline:

```text
READ COMMITTED
```

Strong consistency is not achieved by globally using SERIALIZABLE. It is achieved by combining:

- explicit row locks with predicate-appropriate strength;
- exact PK/UNIQUE authority;
- FK lifetime authority;
- optimistic DRAFT generation checks;
- logical transaction advisory gates for the few global predicates;
- fresh re-read/re-validation after stabilization.

After a lock wait or gate acquisition, a mutation must re-read the relevant current predicate. A candidate derived solely from a pre-lock snapshot cannot be committed without revalidation.

Ordinary single-statement reads use READ COMMITTED snapshot semantics. A multi-statement read that truly requires one stable read snapshot may use `REPEATABLE READ READ ONLY` when it cannot reasonably be expressed as one coherent statement.

SERIALIZABLE is not the current mutation baseline and would require an explicit architecture decision plus retry contract if introduced.

## Lock-strength baseline

When a row is the concurrency owner of a mutation that does not delete the row or modify a referenced key:

```text
SELECT ... FOR NO KEY UPDATE
```

When the mutation deletes the row or changes a referenced key/identity:

```text
SELECT ... FOR UPDATE
```

This distinction preserves same-owner writer exclusion while allowing referential key-share protection to coexist with non-key metadata/state changes when semantics permit it.

### Lifecycle-sensitive dependency admission

When a mutation creates/certifies a new exact dependency that must remain PUBLISHED through commit:

```text
SELECT ... FOR SHARE
```

is taken on the exact dependency row, followed by PUBLISHED recheck.

`FOR KEY SHARE` is insufficient for lifecycle admission because status changes are non-key updates that must conflict with admission.

### Deterministic multi-resource ordering

When equivalent sets of rows must be locked, lock ordering is deterministic. For versioned model dependencies the conceptual ordering key is:

```text
(kind, lineage_uuid, resource_rank, version)
```

with lineage header before exact version for the same lineage when both are required.

Deadlock detection remains a fallback/retry safety mechanism, not the normal semantic serialization strategy.

## Versioned model locking

### Create-next / version allocation

The stable lineage header is the concurrency owner for version-set allocation:

```text
lineage header FOR NO KEY UPDATE
```

After stabilization, `max(existing)+1` and source eligibility are derived from the current version set.

### DRAFT mutation

REVISE/PUBLISH use the exact DRAFT as non-key mutation owner:

```text
exact DRAFT FOR NO KEY UPDATE
```

DRAFT delete uses lineage stabilization plus:

```text
exact DRAFT FOR UPDATE
```

because the exact row is removed.

After locking:

```text
status == DRAFT
revision == expected_revision
```

must still hold.

### Default mutation

Set default:

```text
lineage header FOR NO KEY UPDATE
-> target exact version FOR SHARE
-> recheck PUBLISHED
```

Clear default uses the lineage owner lock.

Implicit default binding:

```text
lineage header FOR SHARE
-> resolve default_version
-> target exact version FOR SHARE
-> recheck PUBLISHED
-> persist exact pin
```

Explicit new binding takes `FOR SHARE` on the selected exact dependency and rechecks PUBLISHED.

### Publish active consumer

ObjectTemplate publication stabilizes the consumer DRAFT and then locks every direct lifecycle-sensitive exact dependency with `FOR SHARE` in deterministic order before PUBLISHED recheck.

The entire transitive dependency graph is not locked: direct active-model validity is sufficient because each PUBLISHED dependency-owning model is itself certified.

### Deprecation

Exact-version deprecation stabilizes lineage/default/lifecycle state, then checks direct active PUBLISHED consumers. It cannot commit if it would break the active model graph.

### Whole-lineage delete

The lineage header is taken `FOR UPDATE`. Semantic blockers are checked in the UoW and cross-aggregate `RESTRICT` FKs remain the final race authority against references that win concurrently.

## Object concurrency

The Object row is concurrency owner for complete intrinsic current state.

```text
RENAME / DATA_CHANGE / SCHEMA_CHANGE
    -> Object FOR NO KEY UPDATE

DELETE
    -> Object FOR UPDATE
```

After lock acquisition the complete current Object is reloaded and the candidate is rederived/revalidated from the stabilized state.

SCHEMA_CHANGE additionally admits the target exact PUBLISHED ObjectTemplateVersion through `FOR SHARE`.

## Ownership concurrency

The parent Object row is the local concurrency owner for:

```text
ATTACH(parent)
DETACH(parent)
SCHEMA_CHANGE(parent)
```

using `FOR NO KEY UPDATE`.

This serializes current parent exact schema and outgoing ownership-edge state.

### Single-owner authority

The child is not generically Object-row locked solely for ATTACH. Final different-owner exclusion is the ownership table `PRIMARY KEY(child_object_id)` together with fresh semantic re-evaluation.

### Ownership cycle gate

A real ownership edge addition acquires a transaction advisory gate representing ownership-graph writes:

```text
pg_advisory_xact_lock(OWNERSHIP_GRAPH_WRITE_GATE)
```

After waiting on the gate, ownership/cycle predicates are re-read in a **subsequent statement** so READ COMMITTED observes a fresh protected graph snapshot.

DETACH does not take the cycle-add gate because removing an edge cannot create a cycle.

## RelationshipDefinition concurrency

CREATE/RENAME can alter the globally certified Definition interpretation set and therefore use a transaction advisory conflict gate.

Conceptual RENAME ordering:

```text
Definition header FOR NO KEY UPDATE
-> global Definition conflict gate
-> fresh complete/global conflict read
-> atomic complete Resolution-name update
```

Resolution names are non-key metadata; RENAME deliberately does not require key-changing row locks solely because factual runtime rows reference Resolution identity.

Definition DELETE takes its header `FOR UPDATE` and relies on `RESTRICT` factual-reference lifetime authority. It does not need the global conflict gate because removal cannot introduce a new equivalence/conflict.

## Runtime Relationship convergence

Equivalent concurrent Relationship CREATE has no pre-existing factual header that can universally serve as lock owner.

The baseline therefore uses exact-view uniqueness rather than a global Relationship graph lock:

```text
load selected Resolution + endpoint Objects
-> validate stable-lineage admission
-> lookup exact current view
-> if present: converge
-> else derive complete closure
-> attempt aggregate insert
```

Final collision authority:

```text
PRIMARY KEY (resolution_id, from_object_id, to_object_id)
```

A colliding candidate UoW is rolled back completely and the semantic operation restarts in a fresh UoW. Fresh re-evaluation either converges on the current winner or creates a new factual identity if no equivalent fact remains.

Relationship DELETE takes the factual Relationship header `FOR UPDATE`, reloads the complete current closure and required semantic-view event set, then atomically deletes closure/header and emits the real deletion events.

## Referential lifetime

Immediate PostgreSQL FK `RESTRICT` is a final correctness authority for current cross-aggregate references.

```text
reference wins
    -> target delete cannot commit

target delete wins
    -> new reference cannot commit

reference removed first
    -> delete may become admissible
```

Semantic admission is still performed by the owning UoW; FK failure is the final race backstop, not a substitute for domain validation.

## Lifecycle-event atomicity and snapshots

Required lifecycle events are inserted in the same write UoW as the semantic mutation.

No current-state transition may commit without its complete required real event set, and no event set may commit for a mutation that rolled back.

Relationship event metadata is observed coherently. Definition rename and Relationship factual transition do not need generic serialization when snapshot coherence can be achieved through the designed observation/locking path.

## Parallelism policy

The architecture accepts some intentional over-serialization where it simplifies correctness, provided semantic independence remains documented and verified.

It also protects intended non-serialization where stronger locks would create unnecessary coupling. A key example is keeping `RelationshipResolution.name` out of FK-referencable key structures so pure Definition rename does not unnecessarily block runtime Relationship FK insertion.

Correctness predicates dominate throughput; lock strength should still be no stronger than required by the predicate defined in `concurrency-matrix.md`.

# M4 WIP — Object optimistic preparation with aggregate fingerprint

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records an agreed concurrency/execution pattern for expensive Object mutations, discovered while designing `Object.SCHEMA_CHANGE`.

The goal is to move expensive candidate construction and semantic validation outside the mutation Unit of Work while preserving the existing complete-Object-state concurrency guarantee.

## Core pattern

An expensive Object mutation may proceed in two phases:

```text
PREPARE OPTIMISTICALLY
    read one coherent current aggregate snapshot S
    compute a deterministic fingerprint F(S)
    perform expensive semantic work outside locks
    produce complete candidate C derived from S

COMMIT PESSIMISTICALLY
    enter short mutation UoW
    acquire the Object concurrency-owner lock
    re-read/recompute current aggregate fingerprint F(S')

    if F(S') != F(S)
        -> rollback
        -> bounded restart from preparation

    if F(S') == F(S)
        -> prepared candidate is still based on the current aggregate generation
        -> perform final mutable admission checks
        -> persist candidate + required lifecycle state atomically
```

The protocol is deliberately conservative. A change to aggregate state that did not actually affect the prepared semantic candidate may still invalidate the fingerprint and cause a restart.

That false-positive restart is accepted in exchange for a simpler, safer and more reusable concurrency protocol.

## Why conservative whole-aggregate fingerprinting is preferred

The fingerprint does not need to be mutation-specific.

For example, `Object.SCHEMA_CHANGE` may not semantically depend on `canonical_name`, but a concurrent rename may still change the aggregate fingerprint and force a restart.

```text
SCHEMA_CHANGE prepares from snapshot S
RENAME commits
protected fingerprint differs
    -> SCHEMA_CHANGE restarts
```

This is intentionally acceptable.

The expected rate of such false restarts is considered much less important than keeping the concurrency rule easy to understand, verify and reuse.

The M4 direction is therefore:

> prefer one conservative Object aggregate fingerprint over a family of mutation-specific dependency fingerprints unless later evidence proves the false-restart cost materially harmful.

## Aggregate-state scope

"Whole Object" means the authoritative state owned by the Object aggregate/concurrency owner, not every enriched public projection reachable from the Object.

Strong candidate snapshot contents:

```text
Object intrinsic state
    id
    canonical_name
    template_id
    template_version
    properties

outgoing ownership facts owned by the Object as parent
    child_object_id
    slot_declaring_template_id
    slot_name
```

The outgoing ownership set must use deterministic ordering before fingerprinting, for example:

```text
(slot_declaring_template_id, slot_name, child_object_id)
```

Derived/read-enrichment data is excluded. Examples:

```text
child canonical_name
child properties
child schema metadata
ObjectTemplate display metadata
Relationship state
lifecycle history
```

Those values belong to other aggregates/read models or are not mutation-owned current Object state.

The exact final aggregate fingerprint scope must be reconciled with the final M4 Object ownership/concurrency model, but the conservative principle is frozen.

## SCHEMA_CHANGE consequence

For Object schema migration this pattern allows almost all expensive work to happen before the short mutation UoW.

Outside the UoW:

```text
read Object aggregate snapshot S
compute F(S)

load/cache immutable MigrationPlan(source,target)

apply plan to S
    optional/required decisions
    SCALAR -> LIST conversion where required
    target exact-DTV validation
    target canonicalization
    target property-state construction
    ownership compatibility analysis

produce complete PreparedSchemaChange candidate
```

Inside the UoW:

```text
lock Object concurrency owner
recompute/read current aggregate fingerprint F(S')

mismatch
    -> rollback + bounded restart

match
    -> no expensive migration recomputation is required
    -> perform final target-PUBLISHED admission/protection
    -> persist exact target binding + target properties
    -> persist lifecycle event(s)
    -> commit
```

The same principle may later be evaluated for other expensive Object mutations.

## Relationship to semantic concurrency contract

The current semantic concurrency contract requires complete Object transitions to be serially explainable and candidates not to commit from stale Object state.

This protocol realizes that requirement by ensuring:

```text
prepared candidate C was derived from snapshot S
+
protected current snapshot S' is equivalent to S
+
Object concurrency-owner lock prevents later Object-generation change before commit
```

Therefore the candidate may commit without being fully rederived under lock.

If the snapshots differ, the candidate is discarded and preparation restarts from fresh state.

## Fingerprint vs exact snapshot equality

The semantic requirement is equivalence of the protected current aggregate generation with the aggregate generation used for preparation.

The implementation may realize this with a fingerprint/hash, but M4 does not yet freeze a concrete hash algorithm.

Required fingerprint properties:

```text
deterministic
stable across irrelevant serialization/order differences
cheap to compute
collision risk / equivalence quality appropriate for concurrency safety
same logical aggregate state -> same fingerprint
changed logical aggregate state -> practically guaranteed different fingerprint
```

Implementation candidates may include database-side or application-side hashing/fingerprinting, but are deferred to physical/performance verification.

## Hashing efficiency is the important optimization question

Because optimistic preparation already needs the aggregate snapshot, the first fingerprint can usually be computed with little incremental I/O cost.

The more important hot-path question is the protected recheck inside the UoW.

A desirable physical direction is:

```text
acquire Object lock
compute deterministic current aggregate fingerprint close to the database
return only the compact fingerprint when practical
```

rather than transferring/reconstructing expensive aggregate state solely to check freshness.

The exact PostgreSQL query shape, canonical encoding and hash/fingerprint function require benchmark/evidence before freeze.

## Bounded retry

Fingerprint mismatch is an approved internal optimistic-restart condition.

Retries must be bounded.

```text
mismatch
    -> no partial mutation
    -> rollback current UoW
    -> re-read fresh aggregate snapshot
    -> recompute fingerprint
    -> redo preparation against fresh state
```

The exact retry count/backoff policy belongs to the later concurrency/implementation closure.

## Frozen discovery decision

M4 adopts the following design direction for expensive Object mutation preparation:

```text
1. read coherent whole-aggregate source snapshot outside the mutation UoW
2. compute deterministic aggregate fingerprint
3. perform expensive candidate construction/validation outside locks
4. enter short UoW and lock Object concurrency owner
5. recompute protected current aggregate fingerprint
6. fingerprint mismatch -> rollback + bounded restart
7. fingerprint match -> use prepared candidate without full recomputation
8. perform remaining current mutable admissions and atomic persistence
```

False-positive restarts caused by changes irrelevant to one specific mutation are acceptable by design.

The priority is protocol simplicity, correctness and efficient fingerprint computation, not minimizing every possible restart through mutation-specific fingerprint scopes.

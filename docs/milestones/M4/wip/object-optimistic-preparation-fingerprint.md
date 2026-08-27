# M4 WIP — Object optimistic preparation with aggregate fingerprint

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records an agreed concurrency/execution pattern for expensive Object mutations, discovered while designing `Object.SCHEMA_CHANGE`.

The goal is to move expensive candidate construction and semantic validation outside the mutation Unit of Work while preserving the complete-Object-state concurrency guarantee.

## Core safety priority

The protocol is intentionally asymmetric:

```text
false SUCCESS
    -> forbidden strongly
    -> a mutation must never commit from stale aggregate state

false FAILURE
    -> acceptable conservatively
    -> a failure may be returned from a coherent earlier committed snapshot
       even if a concurrent mutation later removes the blocker
```

The primary correctness objective is therefore:

> protect successful state transitions strongly; do not pay extra locking/recheck cost merely to eliminate statistically rare conservative failures that cannot make the persisted data model inconsistent.

A caller may retry after a conservative failure and be admitted against the newer state.

## Core pattern

An expensive Object mutation may first prepare optimistically:

```text
PREPARE OPTIMISTICALLY
    read one coherent current aggregate snapshot S
    compute a deterministic fingerprint F(S)
    perform expensive semantic work outside locks
```

Preparation may produce either a semantic failure or a complete candidate.

### Prepared semantic failure

If snapshot `S` itself proves that the requested mutation is currently inadmissible:

```text
prepare(S) -> FAILURE
```

the command may return that failure immediately.

It does not have to acquire the Object lock or recheck `F(S)` solely to determine whether a concurrent mutation removed the blocker after `S` was read.

Example:

```text
T1 SCHEMA_CHANGE reads S
    removed component slot still has child eth0
    -> migration blocked

T2 DETACH eth0 commits

T1 may still return the already-derived failure
```

This is an approved conservative stale failure. It never commits invalid state.

### Prepared successful candidate

If preparation derives a candidate that could mutate persisted state:

```text
prepare(S) -> candidate C
```

then success must be protected strongly:

```text
COMMIT PESSIMISTICALLY
    enter short mutation UoW
    acquire the Object concurrency-owner lock
    re-read/recompute current aggregate fingerprint F(S')

    if F(S') != F(S)
        -> C must not commit
        -> rollback
        -> bounded restart from fresh preparation

    if F(S') == F(S)
        -> C is still based on the current aggregate generation
        -> perform final mutable admission checks
        -> persist candidate + required lifecycle state atomically
```

Thus:

```text
stale prepared success
    -> forbidden

stale prepared failure
    -> acceptable
```

## Why conservative whole-aggregate fingerprinting is preferred

The fingerprint does not need to be mutation-specific.

For example, `Object.SCHEMA_CHANGE` may not semantically depend on `canonical_name`, but a concurrent rename may still change the aggregate fingerprint and force a restart of a prepared successful candidate.

```text
SCHEMA_CHANGE prepares candidate C from S
RENAME commits
protected fingerprint differs
    -> C cannot commit
    -> SCHEMA_CHANGE restarts
```

This false-positive restart is intentionally acceptable.

The expected rate of such restarts is considered much less important than keeping the concurrency rule easy to understand, verify and reuse.

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

The exact final aggregate fingerprint scope must be reconciled with the final M4 Object ownership/concurrency model, but the conservative whole-aggregate principle is frozen.

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
```

If this analysis proves the migration invalid on `S`, the command may fail immediately without entering the commit UoW.

If it produces a complete `PreparedSchemaChange` candidate, only then is the protected success path needed:

```text
lock Object concurrency owner
recompute/read current aggregate fingerprint F(S')

mismatch
    -> prepared candidate cannot commit
    -> rollback + bounded restart

match
    -> no expensive migration recomputation required
    -> perform final target-PUBLISHED admission/protection
    -> persist exact target binding + target properties
    -> persist lifecycle event(s)
    -> commit
```

The same principle may later be evaluated for other expensive Object mutations.

## Relationship to semantic concurrency contract

A committed Object transition must be explainable from current protected state.

For a successful prepared candidate the protocol establishes:

```text
candidate C was derived from snapshot S
+
protected current snapshot S' is equivalent to S
+
Object concurrency-owner lock prevents later Object-generation change before commit
```

Therefore `C` may commit without being fully rederived under lock.

A semantic failure has no equivalent freshness obligation because it performs no state transition. Returning a failure that was true on coherent committed snapshot `S` cannot violate persisted invariants even if later concurrent work would have made a retry succeed.

## Fingerprint vs exact snapshot equality

The semantic requirement for successful commits is equivalence of the protected current aggregate generation with the aggregate generation used for preparation.

The implementation may realize this with a fingerprint/hash, but M4 does not yet freeze a concrete hash algorithm.

Required fingerprint properties:

```text
deterministic
stable across irrelevant serialization/order differences
cheap to compute
collision risk / equivalence quality appropriate for strong commit safety
same logical aggregate state -> same fingerprint
changed logical aggregate state -> practically guaranteed different fingerprint
```

Implementation candidates may include database-side or application-side hashing/fingerprinting, but are deferred to physical/performance verification.

## Hashing efficiency is the important optimization question

Because optimistic preparation already needs the aggregate snapshot, the first fingerprint can usually be computed with little incremental I/O cost.

The more important hot-path question is the protected recheck for a prepared candidate inside the UoW.

A desirable physical direction is:

```text
acquire Object lock
compute deterministic current aggregate fingerprint close to the database
return only the compact fingerprint when practical
```

rather than transferring/reconstructing expensive aggregate state solely to check freshness.

Prepared failures avoid this protected fingerprint cost entirely when no state transition is attempted.

The exact PostgreSQL query shape, canonical encoding and hash/fingerprint function require benchmark/evidence before freeze.

## Bounded retry

Fingerprint mismatch on the successful-candidate path is an approved internal optimistic-restart condition.

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

A prepared semantic failure is not an internal fingerprint retry condition. It may be returned directly to the caller; a later caller retry is a new command attempt against newer state.

## Frozen discovery decision

M4 adopts the following design direction for expensive Object mutation preparation:

```text
1. read coherent whole-aggregate source snapshot S outside the mutation UoW
2. compute deterministic aggregate fingerprint F(S)
3. perform expensive semantic analysis/candidate construction outside locks

4a. if analysis(S) proves FAILURE
        -> failure may be returned immediately
        -> no lock/fingerprint recheck required merely to detect blocker disappearance
        -> conservative false failure is acceptable

4b. if analysis(S) produces successful candidate C
        -> enter short UoW
        -> lock Object concurrency owner
        -> recompute protected current fingerprint F(S')

5. F(S') != F(S)
        -> C must not commit
        -> rollback + bounded restart

6. F(S') == F(S)
        -> use prepared C without full recomputation
        -> perform remaining current mutable admissions
        -> persist state + lifecycle atomically
```

Additional frozen priorities:

```text
false success protection
    -> STRONG

false failure elimination
    -> not a correctness requirement
    -> statistically rare conservative failures are acceptable

whole-aggregate false-positive restart
    -> acceptable

priority
    -> data-model consistency
    -> protocol simplicity
    -> short lock-held UoW
    -> efficient fingerprint computation
    -> only then reduction of rare false failures/restarts
```

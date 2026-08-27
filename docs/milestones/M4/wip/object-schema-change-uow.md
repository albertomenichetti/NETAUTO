# M4 WIP — Object SCHEMA_CHANGE short mutation UoW

Status: PARTIAL FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the route-local mutation-UoW decisions frozen incrementally for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

The expensive migration work is prepared outside the mutation UoW from one coherent Object aggregate snapshot `S` and an immutable `MigrationPlan(source,target)`. The short UoW exists to prevent stale prepared success, hold final mutable admission authorities through commit, persist the already-prepared target Object state and write the required lifecycle transition atomically.

## Prepared input

A successful preparation produces a compact candidate conceptually equivalent to:

```text
PreparedSchemaChange
    object_id
    template_id
    source_version
    target_version
    expected_object_fingerprint
    target_properties
    lifecycle_before
    lifecycle_after
```

`target_properties` has already been fully migrated, validated and canonicalized outside the UoW.

Ownership/component analysis also happens outside the UoW. Under the normal M4 schema-evolution contract, an admitted Object schema change never mutates `object_components`:

```text
ADD slot
    -> new slot starts empty

REMOVE slot
    -> blocking current edge => preparation failure
    -> otherwise no ownership DML

continuous target widening
    -> existing edges remain valid by construction

position-only change
    -> ownership facts unchanged

semantic-identity replacement
    -> blocking old-slot edge => preparation failure
    -> otherwise new semantic slot starts empty
```

Therefore a prepared success contains no `edges_to_keep`, `edges_to_delete`, `edges_to_rebind` or target ownership state to persist.

## Conservative failure / strong success asymmetry

The optimistic-preparation protocol deliberately treats negative and positive decisions differently:

```text
prepared failure
    -> may return immediately from the preparatory snapshot
    -> no lock/fingerprint recheck required
    -> conservative stale false failure is acceptable

prepared success
    -> MUST NOT commit unless the protected current aggregate still matches
       the exact aggregate generation used for preparation
```

The priority is strong prevention of false success. A stale failure cannot make persisted state incoherent; a stale success can.

## Required UoW serialization points

### Exact TARGET ObjectTemplateVersion

The exact target ObjectTemplateVersion is a lifecycle-sensitive new binding admission.

The UoW must hold the exact target row in a mode equivalent to:

```text
TARGET ObjectTemplateVersion @ FOR SHARE
```

and recheck:

```text
same template_id
exact target_version
target status == PUBLISHED
```

while protected.

This hold must remain through commit. It rendezvous with target deprecation/lifecycle mutation and prevents this schema-change transaction from successfully creating a new Object binding to a target that stops being `PUBLISHED` before the mutation commits.

The SOURCE exact OTV is an already-existing historical binding and may be `PUBLISHED` or `DEPRECATED`; it is not a new admission and does not require a new PUBLISHED hold merely because the Object is migrating away from it.

### Parent Object concurrency owner

The parent Object row is the concurrency owner for this mutation and must be held in a mode equivalent to:

```text
Object @ FOR NO KEY UPDATE
```

This lock serializes `SCHEMA_CHANGE` with intrinsic Object mutation and, critically, with ownership mutation of the same parent.

It is the rendezvous point with at least:

```text
SCHEMA_CHANGE
DATA_CHANGE
RENAME
ATTACH
DETACH
```

`DELETE` uses a stronger Object lock and therefore also serializes.

The parent-Object lock is not only about `template_version`/`properties`. It is required so that outgoing ownership facts represented in the preparatory aggregate fingerprint cannot change between the protected fingerprint recheck and commit.

## ATTACH / DETACH serialization guarantee

The intended serial outcomes are:

```text
ATTACH commits first
    -> SCHEMA_CHANGE protected fingerprint differs from preparation when
       the new edge changed the aggregate
    -> prepared success cannot commit stale
    -> rollback + bounded restart
    -> retry observes/preserves-or-rejects the new edge

SCHEMA_CHANGE commits first
    -> concurrent ATTACH waits on the parent Object
    -> after wake-up ATTACH must re-evaluate the parent's current exact schema
       and validate the requested slot against the post-migration binding

DETACH commits first
    -> it may remove a blocker before a later fresh schema-change preparation

SCHEMA_CHANGE commits first
    -> concurrent DETACH waits and then operates against the post-migration
       parent state according to DETACH's own fresh-state contract
```

Therefore `SCHEMA_CHANGE`, `ATTACH` and `DETACH` must rendezvous on the same parent-Object concurrency owner.

## Lock ordering

The mutation must respect the global target-before-current-owner ordering used by the kernel concurrency model:

```text
1. exact TARGET ObjectTemplateVersion admission hold
2. parent Object concurrency-owner lock
```

The exact physical lock plan will be reconciled globally during the M4 concurrency/physical-design closure. Route-local semantics require the target lifecycle authority to be protected before Object DML and the Object owner to remain protected through commit.

Whether a stable ObjectTemplate-header row lock is still necessary in the M4 TO-BE realization is intentionally not frozen here. This route does not use mutable default/header policy during explicit target-version migration; any header hold must be justified later by reference-lifetime/delete-lineage mechanics rather than inherited blindly from the AS-IS lock registry.

## Protected fingerprint check

After acquiring the parent Object concurrency-owner lock, the transaction recomputes or reads the authoritative current aggregate fingerprint `F(S')` covering the agreed whole-Object aggregate state.

```text
F(S') != expected_object_fingerprint
    -> prepared success is stale
    -> no Object or lifecycle DML
    -> rollback
    -> bounded restart from fresh preparation

F(S') == expected_object_fingerprint
    -> prepared candidate is still based on the current aggregate generation
    -> no expensive property migration or component compatibility analysis is repeated
```

The whole-aggregate fingerprint is deliberately conservative. A concurrent change that did not actually alter the semantic migration result may still cause a retry; this is accepted in exchange for a simple strong success guard.

## Post-lock statement-snapshot boundary

The parent Object lock acquisition and the protected aggregate fingerprint read are intentionally **separate PostgreSQL statements** under `READ COMMITTED`.

The reason is that a statement that begins before waiting for the Object lock retains its own statement snapshot. If `SCHEMA_CHANGE` attempted to lock the parent and inspect all fingerprint state in that same statement, a concurrent `ATTACH` or `DETACH` could commit while `SCHEMA_CHANGE` is waiting, yet the waiting statement could continue to observe the pre-wait snapshot for non-locked ownership rows.

The required pattern is therefore:

```text
Q1
    acquire/protect exact TARGET OTV @ SHARE
    require status == PUBLISHED

Q2
    acquire parent Object @ NO KEY UPDATE
    wait if another parent mutation owns the row

Q2 completes
    -> Object concurrency owner is now held

Q3 — NEW PostgreSQL statement
    -> new READ COMMITTED statement snapshot
    -> read/recompute the authoritative whole-Object aggregate fingerprint
       including outgoing ownership facts
```

Example race:

```text
T2 ATTACH
    holds parent Object @ NKU
    inserts edge eth0

T1 SCHEMA_CHANGE
    Q2 attempts parent Object @ NKU
    -> waits

T2 commits

T1 Q2 acquires the Object lock

T1 Q3 begins as a new statement
    -> its READ COMMITTED snapshot sees T2's committed eth0 edge
    -> fingerprint differs from the preparatory fingerprint
    -> prepared success cannot commit
```

This statement boundary is part of the strong false-success guarantee. It is not merely a query-shape preference.

Frozen rule:

```text
Object lock acquired
    !=
protected fingerprint already fresh

Object lock acquisition statement completes
    -> start a new statement
    -> obtain fresh protected aggregate fingerprint
```

Once Q3 observes a matching fingerprint, the held parent Object lock prevents `DATA_CHANGE`, `SCHEMA_CHANGE`, `RENAME`, `ATTACH`, `DETACH` and `DELETE` from changing the aggregate generation before this transaction commits.

Therefore after a successful protected fingerprint match the mutation does not need to reread current properties or ownership facts again before persistence.

## UoW shape frozen so far

Conceptually:

```text
BEGIN

Q1. acquire/protect exact TARGET OTV
       require status == PUBLISHED
       hold through commit

Q2. acquire parent Object @ NO KEY UPDATE
       serializes intrinsic + parent ownership mutations
       wait if necessary

Q3. NEW statement after Q2 completed
       recompute authoritative aggregate fingerprint F(S')
       from a fresh READ COMMITTED statement snapshot

    if F(S') != prepared F(S)
       -> ROLLBACK
       -> bounded retry from preparation

    if F(S') == prepared F(S)
       -> use already-prepared target_properties / lifecycle snapshots
       -> no property migration re-execution
       -> no component/child revalidation
       -> no object_components DML

Q4. UPDATE Object current exact binding + canonical properties

Q5. INSERT SCHEMA_CHANGE lifecycle transition

COMMIT
```

The remaining route-local work is to close:

```text
- exact final SQL shape for target admission, fingerprint computation,
  Object update and lifecycle insert;
- whether Q4 Object UPDATE and Q5 lifecycle INSERT should remain separate or be
  fused without changing atomic semantics;
- no-op / same-or-lower target-version classification and exact public failures;
- bounded retry boundary and exhaustion mapping;
- lifecycle event payload details under the prepared-candidate model;
- warm/cold DB/cache cost;
- final physical index/EXPLAIN handoff;
- global confirmation of whether the AS-IS OT header lifetime hold is still
  required in the M4 TO-BE physical lock plan.
```

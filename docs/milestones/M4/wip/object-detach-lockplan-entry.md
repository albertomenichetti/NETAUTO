# M4 WIP — Object DETACH LockPlan entry

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the route-local entry into the mutation Unit of Work for the M4 Object DETACH command after revalidation against the current AS-IS concurrency architecture.

Public command shape:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

with one non-empty duplicate-free `child_object_ids` batch.

This note does not yet freeze the complete DETACH statement count or the shape of the protected ownership-state read, delete, lifecycle write, or final failure precedence.

## AS-IS authority revalidated

The current centralized concurrency architecture registers:

```text
OBJ.DET
    gate = none
    row plan = parent Object OBJ@NKU
```

The parent Object is therefore the existing concurrency owner for DETACH against same-parent ownership mutation and parent SCHEMA_CHANGE.

The M4 design keeps that ownership model rather than introducing route-local parent SHARE locking or a new ownership-edge lock class.

## No PostgreSQL preparation before the plan

The DETACH LockPlan is completely known from the public path target:

```text
parent_object_id
```

No candidate-dependent model dependency, ancestry set, graph gate, template version, child lock, or ownership-edge lock must be discovered before the initial plan can be constructed.

Therefore normal DETACH performs:

```text
PostgreSQL preparation before BEGIN / LockPlan acquisition = 0 statements
```

Static transport validation remains outside this count.

## Initial LockPlan

```text
LockPlan
    gate = none
    rows = [parent Object @ NKU]
```

The centralized planner remains responsible for lock mode realization, row-class ordering, deterministic UUID ordering, missing planned-row reporting, and the no-post-DML-lock-append discipline.

DETACH must not bypass this planner by issuing an equivalent route-private `FOR NO KEY UPDATE` statement.

## Q1 — centralized plan acquisition

The first PostgreSQL business operation of the mutation UoW is the centralized LockPlan acquisition for the parent Object.

Conceptually:

```text
BEGIN

Q1  acquire LockPlan
    parent Object @ FOR NO KEY UPDATE
```

Outcome:

```text
parent planned row missing
    -> rollback
    -> 404 resource_not_found

parent acquired
    -> retain lock through the UoW
    -> continue to one fresh protected ownership-state read
```

The missing-row outcome comes from the planner's normal exact-row acquisition contract; no preliminary parent existence SELECT is required.

## Why no route-local parent SHARE lock

An earlier M4 WIP direction proposed `FOR SHARE` inside DETACH's delete statement purely to rendezvous with SCHEMA_CHANGE. That is superseded.

The AS-IS architecture already defines the stronger and centralized rule:

```text
DETACH / ATTACH / parent SCHEMA_CHANGE
    -> parent Object concurrency owner
```

and specifically registers `OBJ.DET` with `OBJ@NKU`.

Keeping that rule:

- preserves the centralized LockPlan as the sole ordering/mode authority;
- serializes overlapping DETACH batches on the same parent before edge DML;
- serializes DETACH with parent SCHEMA_CHANGE under `PO`;
- serializes parent DELETE through `OBJ@U` under the same Object row;
- avoids inventing a second route-local lock protocol.

## Fresh protected state is still required

Acquiring the parent row does not itself certify the requested ownership batch.

After Q1, DETACH must execute a new READ COMMITTED statement that observes the authoritative current ownership state after any wait on the parent lock.

No ownership admission decision may rely solely on an unlocked snapshot captured before Q1.

The exact Q2 data set and result carrier are intentionally left for the next route-local decision.

## Frozen decision

```text
DETACH PostgreSQL preparation before LockPlan = 0 statements

first DB operation:
    centralized LockPlan acquisition

initial plan:
    gate = none
    parent Object @ NKU

missing planned parent:
    -> 404 resource_not_found

no route-local FOR SHARE replacement
no new ownership-edge RowLockClass for DETACH
no pre-plan ownership/schema query

next step after Q1:
    one fresh protected ownership-state read
```

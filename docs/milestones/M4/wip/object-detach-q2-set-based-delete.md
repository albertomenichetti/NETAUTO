# M4 WIP — Object DETACH Q2 set-based certification + delete

Status: FROZEN DISCOVERY INPUT / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note records the current route-local candidate for the second PostgreSQL statement of Object DETACH after the parent has already been stabilized by the preceding candidate Q1.

Public command surface under discovery:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

with a non-empty duplicate-free `child_object_ids` batch.

The batch candidate remains strict/non-convergent and atomic: every requested child must exist and must currently own the exact requested parent/slot edge, otherwise the whole transaction is rolled back.

This is WIP discovery material. It is not architecture authority and remains subject to architecture-phase revalidation.

## Candidate responsibility split

Current candidate sequence:

```text
BEGIN

Q1  parent stabilization / concurrency handoff

Q2  fresh child-operand classification
    + exact-edge bulk DELETE
    + RETURNING lifecycle material

Q3  bulk DETACH_FROM lifecycle INSERT

COMMIT
```

Because Q1 already establishes path-target parent existence/stability, Q2 does not need to perform a second independent parent-existence admission check.

## Q2 input

```text
parent_object_id
slot_name
requested child_object_ids[N]
```

Request ordering has no semantic meaning.

`slot_declaring_template_id` is not supplied by the caller. It is materialized on the candidate TO-BE `object_components` row and is obtained from the exact edge actually deleted.

## Q2 logical result contract

One fresh PostgreSQL statement must return enough information for both admission and Q3 lifecycle emission:

```text
parent_canonical_name

missing_child_ids[]

deleted_edges[]:
    child_object_id
    child_canonical_name
    parent_object_id
    slot_declaring_template_id
    slot_name
```

The exact SQL carrier, aggregation shape and application mapping remain implementation details.

## Candidate set-based shape

Conceptually Q2 performs, in one statement/snapshot:

```text
requested
    -> materialize the N requested child ids

children
    -> LEFT JOIN requested ids to objects
    -> determine missing child operands
    -> obtain existing child canonical_name values required by lifecycle

deleted
    -> DELETE matching object_components rows
       WHERE:
           child_object_id is requested
           parent_object_id = requested parent
           slot_name = requested slot

       RETURNING:
           child_object_id
           parent_object_id
           slot_declaring_template_id
           slot_name

final result
    -> missing_child_ids
    -> deleted edge rows enriched with required display metadata
    -> current parent canonical_name required by lifecycle
```

No ObjectTemplate/effective-schema/ancestry data participates in Q2.

## Exact-edge matching

The public request identifies the edge through:

```text
parent_object_id
slot_name
child_object_id
```

Therefore the DELETE predicate does not require a caller-provided `slot_declaring_template_id`.

The candidate persisted edge remains richer:

```text
child_object_id
parent_object_id
slot_declaring_template_id
slot_name
```

and `slot_declaring_template_id` is returned from the row actually deleted for lifecycle semantic identity.

## Admission after Q2

Application-side classification uses only Q2's required execution result:

```text
missing_child_ids is non-empty
    -> ROLLBACK
    -> 422 referenced_resource_not_found

missing_child_ids is empty
AND len(deleted_edges) < requested_count
    -> ROLLBACK
    -> 409 ownership_conflict

len(deleted_edges) == requested_count
    -> execute Q3 bulk DETACH_FROM lifecycle INSERT
```

`ownership_conflict` continues to cover existing-child cases where the requested exact edge is not current, including:

```text
child ownerless
child owned by another parent
child owned by same parent under another slot
```

No extra PostgreSQL query is issued to distinguish those subcases.

## Delete-first certification and rollback

Q2 deliberately prefers:

```text
DELETE exact matching rows
RETURNING actual deleted set
then certify complete batch from the returned result
```

over:

```text
SELECT/pre-certify all exact edges
then issue a second DELETE over the same facts
```

Rationale:

- avoids a success-path round trip;
- avoids re-reading the same ownership facts solely to delete them afterward;
- optimizes the expected successful data-plane path;
- preserves strict batch semantics through transaction rollback.

Example:

```text
requested = 100
matching current exact edges = 99

Q2 physically deletes 99 rows inside the open transaction
Q2 result proves deleted_count = 99
application classifies ownership_conflict
ROLLBACK restores all 99 rows
```

No partial DETACH becomes committed.

## Why current Object rows are read

Child Object access is required for the candidate contract, not for diagnostic enrichment alone:

```text
1. distinguish missing referenced child -> 422
   from existing child with non-current exact edge -> 409

2. obtain child.canonical_name for DETACH_FROM lifecycle display metadata
```

The parent canonical name may be obtained in the same Q2 statement because lifecycle requires it. Q1 has already established the parent as the path target; Q2 does not repeat parent admission semantics merely to obtain the display label.

Lifecycle canonical names remain best-effort historical display metadata rather than semantic concurrency identities.

## Q3 handoff

Q3 consumes only Q2 returned material and performs one bulk lifecycle INSERT:

```text
one DETACH_FROM event per deleted edge
```

Q3 does not reread:

```text
parent Object
child Objects
ownership facts
ObjectTemplate state
component schema
ancestry/cache state
```

Q2 + Q3 remain in one transaction, so Q3 failure rolls back Q2 deletions.

## Candidate cost

Ignoring BEGIN/COMMIT and any concurrency realization that remains an architecture handoff:

```text
Q1 parent stabilization
Q2 set-based certification + bulk DELETE + RETURNING
Q3 bulk lifecycle INSERT

candidate success path = 3 PostgreSQL statements
```

The round-trip count is constant with respect to requested child count; row volume scales with N.

Per project governance this WIP cost is a candidate data-path estimate, not a normative transaction/locking budget.

## Supersession / reconciliation note

Earlier DETACH WIPs assigned parent existence, edge deletion and failure classification to a single first business statement and described a two-statement total UoW. The current discovery sequence has since introduced a preceding parent-stabilization Q1.

This note therefore supersedes only those older statement-numbering/responsibility assumptions for the current candidate data path. Their retained semantic findings — strict batch atomicity, referenced-child vs ownership-conflict distinction, bulk lifecycle write and no diagnostic-only DB queries — remain discovery inputs subject to later revalidation.

## Architecture handoff

Future architecture closure must compose this candidate with the final M4 concurrency/transaction realization and re-prove all affected strong-consistency guarantees, including relevant ownership-fact and reference-lifetime races.

The discovery candidate itself does not prescribe the final LockPlan realization.

## Frozen discovery takeaway

```text
Q2 = one fresh set-based PostgreSQL statement

Q2 performs:
    requested-child existence/classification
    exact parent+slot+child bulk DELETE
    RETURNING persisted slot_declaring_template_id
    lifecycle display material capture

missing child -> rollback + 422
existing child but incomplete exact-edge set -> rollback + 409
complete set -> Q3 bulk lifecycle

no schema reconstruction
no pre-certification SELECT + second DELETE
no diagnostic-only reread
```

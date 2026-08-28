# M4 WIP — Object DETACH bulk lifecycle write

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note records the candidate bulk lifecycle write for the current M4 Object DETACH discovery.

Public command surface:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

with a duplicate-free non-empty batch of `child_object_ids`.

This note supersedes the earlier route-local numbering in which lifecycle persistence was Q2 of a two-statement DETACH candidate. The current discovery candidate has a separate preceding parent-stabilization step, so lifecycle persistence is Q3.

## Current candidate UoW shape

```text
BEGIN

Q1  parent stabilization
    -> candidate integration with centralized LockPlan

Q2  fresh set-based requested-child classification
    + exact-edge bulk DELETE
    + RETURNING lifecycle material

Q3  bulk DETACH_FROM lifecycle INSERT
    -> no RETURNING

COMMIT
```

Q3 is executed only when Q2 proves the strict batch complete:

```text
all requested child Objects exist
AND
exactly one requested parent/slot edge was deleted for every requested child id
```

If Q2 reports a missing child or incomplete exact-edge set, the transaction is rolled back before any lifecycle write is attempted.

## Q3 input authority

Q3 consumes only the material already produced by Q2.

For each successfully deleted edge Q2 provides:

```text
child_object_id
child_canonical_name
parent_object_id
parent_canonical_name
slot_declaring_template_id
slot_name
```

Q3 does not reread:

- parent Object;
- child Objects;
- ObjectTemplate state;
- effective component schema;
- ownership state;
- caches.

The deleted ownership fact is the authority for the semantic slot identity. In the M4 candidate physical schema, `slot_declaring_template_id` is already materialized on `object_components`, so DETACH does not reconstruct it from the parent schema.

## Event mapping

For every row deleted by Q2, Q3 inserts exactly one `DETACH_FROM` lifecycle event:

```text
kind                       = DETACH_FROM
object_id                  = child_object_id
canonical_name             = child_canonical_name
destination_object_id      = parent_object_id
destination_canonical_name = parent_canonical_name
slot_declaring_template_id = slot_declaring_template_id
slot_name                  = slot_name
```

Ownership lifecycle events do not carry intrinsic `before_state` / `after_state` snapshots.

The historical structural identity is therefore represented directly by:

```text
child_object_id
parent_object_id
slot_declaring_template_id
slot_name
```

The canonical-name fields remain best-effort historical display labels. DETACH does not introduce additional locks or rereads solely to improve their freshness.

## Bulk realization

Q3 is one bulk INSERT into `object_lifecycle_events` for all deleted edges.

No per-child PostgreSQL INSERT loop is part of the candidate data path.

The database round-trip count therefore remains constant with respect to batch cardinality; only row volume grows with N.

## No RETURNING

Q3 does not need `RETURNING` on the success path.

The public DETACH command returns:

```http
204 No Content
```

and no later step consumes the generated lifecycle row identity or timestamp.

Therefore the candidate avoids returning and decoding rows that are not used:

```text
INSERT N DETACH_FROM rows
    -> PostgreSQL generates lifecycle id
    -> PostgreSQL applies transaction timestamp semantics
    -> application does not fetch the inserted rows back
```

This differs from the current single-event persistence helper, which returns and decodes an `OwnershipLifecycleEvent`; M4 may introduce a bulk write path specialized for mutation commands that do not consume the newly inserted event rows.

## Atomicity

Q2 and Q3 remain in the same transaction.

```text
Q3 succeeds
    -> COMMIT
    -> deleted ownership edges and corresponding DETACH_FROM events become visible together

Q3 fails
    -> ROLLBACK
    -> every Q2 ownership deletion is restored
```

No committed state may contain a successful ownership removal without its corresponding lifecycle event.

## Why Q3 stays separate from Q2

A single data-modifying statement could technically connect:

```text
DELETE ... RETURNING
    -> INSERT lifecycle SELECT ...
```

but the candidate keeps Q3 separate because:

- the database still performs the same N ownership deletes plus N lifecycle inserts;
- combining the operations mainly saves one round trip while materially increasing SQL complexity;
- Q2 failure can terminate the UoW before any lifecycle row work is attempted;
- the simpler split is easier to reason about and inspect while retaining one semantic transaction.

A future architecture or physical-query review may still re-evaluate this tradeoff; this WIP is not normative.

## Failure handling

A Q3 failure triggers normal transaction rollback and known persistence-failure classification.

No PostgreSQL query is executed solely to enrich lifecycle-write diagnostics.

## Candidate cost consequence

For the current DETACH discovery candidate, excluding `BEGIN` / `COMMIT`:

```text
Q1  parent stabilization
Q2  fresh classification + exact-edge bulk DELETE + RETURNING
Q3  bulk DETACH_FROM INSERT without RETURNING

candidate success path = 3 PostgreSQL statements
```

There is no cache warm/cold distinction and statement count does not grow with the number of requested children.

## Frozen discovery takeaway

```text
Q2 authoritative deleted-edge material
    -> complete strict batch only
    -> Q3 one bulk DETACH_FROM INSERT
    -> no RETURNING
    -> no rereads / caches / schema work
    -> same semantic transaction
    -> Q3 failure restores Q2 deletions
```

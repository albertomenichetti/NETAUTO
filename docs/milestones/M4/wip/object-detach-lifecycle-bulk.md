# M4 WIP — Object DETACH bulk lifecycle write

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the second PostgreSQL business statement of the route-local Object DETACH design.

Public command surface:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

with a duplicate-free non-empty batch of `child_object_ids`.

## Frozen UoW shape

DETACH uses two PostgreSQL business statements inside one transaction:

```text
BEGIN

Q1  parent-existence + bulk exact-edge DELETE + RETURNING
Q2  bulk DETACH_FROM lifecycle INSERT

COMMIT
```

Q2 is executed only when Q1 returned exactly one deleted edge for every requested child id.

If Q1 is incomplete, the transaction is rolled back before any lifecycle write is attempted.

## Q2 input authority

Q2 consumes only the rows returned by Q1.

It does not reread:

- parent Object;
- child Objects;
- ObjectTemplate state;
- effective component schema;
- ownership state;
- caches.

The returned edge rows are the authoritative input for lifecycle identity.

## Event mapping

For every row deleted by Q1, Q2 inserts exactly one `DETACH_FROM` lifecycle event:

```text
kind                       = DETACH_FROM
object_id                  = child_object_id
canonical_name             = child_canonical_name
destination_object_id      = parent_object_id
destination_canonical_name = parent_canonical_name
slot_declaring_template_id = deleted edge slot_declaring_template_id
slot_name                  = deleted edge slot_name
```

The two canonical-name fields are historical display labels captured by Q1 and are best-effort in the same sense already frozen for ownership lifecycle events.

The exact semantic identity remains:

```text
child_object_id
parent_object_id
slot_declaring_template_id
slot_name
```

because it derives directly from the edge rows that Q1 actually deleted.

## Atomicity

Q2 runs in the same transaction as Q1.

Therefore:

```text
Q2 succeeds
    -> COMMIT
    -> deleted edges and DETACH_FROM events become visible together

Q2 fails
    -> ROLLBACK
    -> Q1 deletions are undone too
```

No state can commit where an ownership edge was removed without the corresponding lifecycle events.

## Bulk realization

Q2 is one bulk INSERT for all deleted edges.

No per-child INSERT loop is allowed at the database round-trip level.

The number of PostgreSQL business statements therefore does not grow with the number of requested children.

## No diagnostic rereads

A Q2 failure is handled by transaction rollback and the normal known persistence-failure classification.

No PostgreSQL query is executed solely to improve the diagnostics of a lifecycle-write failure.

## Frozen takeaway

```text
Q1 authoritative DELETE ... RETURNING rows
    -> complete batch only
    -> Q2 one bulk DETACH_FROM INSERT
    -> same transaction
    -> Q2 failure restores Q1 deletions
    -> no rereads / caches / extra locks
```

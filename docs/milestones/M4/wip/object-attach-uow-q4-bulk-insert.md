# M4 WIP — Object ATTACH Q4 bulk edge insert

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the Q4 write step of the M4 TO-BE batch Object ATTACH Unit of Work.

The public batch operation is:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

with a non-empty list of `child_object_ids`.

Q1-Q3 have already established the protected context:

```text
Q1 ownership graph write gate
Q2 parent Object lock + prepared-binding equality
Q3 protected ownerless/root cycle admission
```

## Q4 decision

All requested ownership edges are inserted by one PostgreSQL multi-row INSERT statement.

Conceptually:

```sql
INSERT INTO object_components (
    child_object_id,
    parent_object_id,
    slot_declaring_template_id,
    slot_name
)
VALUES
    (:child_1, :parent, :declaring_template, :slot),
    (:child_2, :parent, :declaring_template, :slot),
    ...,
    (:child_n, :parent, :declaring_template, :slot);
```

Exact SQL construction remains an implementation detail, but the frozen requirement is one bulk insert statement rather than one statement per requested child.

## No ON CONFLICT behavior

Q4 deliberately has no convergent/idempotent conflict handling.

In particular:

```text
child already has any ownership row
    -> PRIMARY KEY(child_object_id) violation
    -> statement fails

child already has exactly the requested parent/slot edge
    -> same PRIMARY KEY violation
    -> statement fails
```

This supersedes the earlier ATTACH candidate where an identical current edge converged successfully.

The public command is therefore a strict attach-new-membership mutation rather than an idempotent ensure-membership operation.

## Atomic batch semantics

A multi-row PostgreSQL INSERT is atomic as one statement within the surrounding transaction.

Therefore:

```text
all requested rows valid
    -> all requested ownership rows inserted

any requested row violates a constraint
    -> Q4 fails
    -> transaction is rolled back
    -> no ownership row from this batch commits
```

No partial success is exposed.

## Relational authorities used directly

Q4 relies on PostgreSQL constraints as final arbitration for facts already represented relationally.

Conceptually:

```text
PRIMARY KEY(child_object_id)
    -> one current owner per child

FK child_object_id -> objects.id
    -> child lifetime/existence

FK parent_object_id -> objects.id
    -> parent lifetime/existence

FK slot_declaring_template_id -> object_templates.id
    -> persisted semantic slot-declaring lineage lifetime

CHECK parent_object_id != child_object_id
    -> direct self edge forbidden
```

The transitive no-cycle rule is not delegated to these constraints; it was certified in protected Q3 under the ownership graph edge-add gate.

The parent exact-schema/slot coherence is likewise not delegated to Q4 constraints; it is protected by Q2 parent locking and prepared-binding equality.

## Concurrency consequence

No current-owner SELECT is required before Q4 merely to arbitrate ownership races.

Competing attempts to attach the same currently ownerless child are resolved by the `child_object_id` primary key at write time. One may commit; the other fails and rolls back according to normal constraint/error classification.

Foreign-key enforcement participates in parent/child lifetime races, so Q4 does not add separate Object row locks solely for referenced-object lifetime.

## Cost

For any batch size `N`:

```text
Q4 PostgreSQL business statement count = 1
```

The number of VALUES rows grows with `N`, but the database round-trip count does not.

This is the core population-shaped benefit of batch ATTACH.

## Frozen takeaway

```text
Q4 = one strict multi-row INSERT

no ON CONFLICT
no per-child INSERT loop
no partial success
any PK/FK/CHECK failure -> rollback whole batch
```

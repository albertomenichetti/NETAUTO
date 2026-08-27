# M4 WIP — Object ATTACH UoW Q5 bulk lifecycle write

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes Q5 of the TO-BE batch ATTACH mutation for:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

Q5 executes only after:

```text
Q1 ownership graph write gate acquired
Q2 parent Object locked and exact binding reconfirmed
Q3 protected graph admission succeeded
Q4 one multi-row INSERT persisted every requested ownership edge
```

Q4 is all-or-nothing. Any PK/FK/CHECK violation aborts the batch before Q5.

## Lifecycle granularity

Lifecycle remains edge-oriented, not request-oriented.

For a successful request containing `N` requested child Object ids, Q4 creates exactly `N` new current ownership facts and Q5 creates exactly `N` corresponding `ATTACH_TO` lifecycle events.

There is no request-level aggregate ATTACH event.

Conceptually:

```text
1 successful new edge
    -> 1 ATTACH_TO lifecycle row

N successful new edges
    -> N ATTACH_TO lifecycle rows
```

Because the M4 ATTACH candidate no longer treats an already-owned child as convergent/idempotent success, a successful batch contains no pre-existing edge that needs to be omitted from lifecycle generation.

## Q5 write realization

Q5 is one bulk PostgreSQL INSERT statement into the lifecycle table.

Conceptually:

```text
INSERT object_lifecycle_events (...)
VALUES
    event for child C1,
    event for child C2,
    ...,
    event for child CN
```

No application loop issuing one INSERT per child is allowed on the normal path.

The number of lifecycle rows scales with the batch size, but the PostgreSQL business-statement count for Q5 remains:

```text
1 statement
```

## Atomicity

Q4 ownership facts and Q5 lifecycle rows belong to the same mutation Unit of Work:

```text
Q4 all ownership-edge INSERTs
+
Q5 all ATTACH_TO lifecycle INSERTs
-> COMMIT together
```

If Q5 fails for any reason:

```text
ROLLBACK
```

removes the Q4 ownership facts as well.

Therefore no committed ownership edge may exist without its required ATTACH lifecycle event.

## Event semantic identity

Each event records the same semantic slot identity persisted by Q4:

```text
child_object_id
parent_object_id
slot_declaring_template_id
slot_name
```

The lifecycle schema may additionally retain historical display metadata such as canonical names according to the final Lifecycle contract. Exact display-name freshness is a separate route-local question and is not silently decided by this note.

## Cost property

For a successful batch of any supported size:

```text
Q4 ownership write   = 1 multi-row INSERT statement
Q5 lifecycle write   = 1 multi-row INSERT statement
```

The batch therefore avoids `N` ownership INSERT round trips and `N` lifecycle INSERT round trips.

## Frozen decision

```text
Q5 = one bulk lifecycle INSERT
one event per successfully inserted ownership edge
same UoW as Q4
failure -> rollback complete batch
```

No new relational structure is introduced by Q5 itself.
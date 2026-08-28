# M4 WIP — Object DETACH two-statement UoW direction

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the preferred Unit-of-Work realization direction for batch Object DETACH after the route was established as schema-agnostic and without an explicit parent lock.

Public command shape under review:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

with a non-empty, duplicate-free batch of `child_object_ids` and atomic all-or-nothing semantics.

## Decision criterion

The realization is chosen by actual execution cost and complexity, not by minimizing the statement counter for its own sake.

If one complex statement and two simple bulk statements perform essentially the same database work, prefer the simpler and more readable implementation.

A one-statement data-modifying CTE is justified only if it produces a meaningful measured benefit beyond saving one client/database round-trip.

## Frozen direction

Prefer two simple bulk business statements on the successful mutation path:

```text
BEGIN

Q1  bulk DELETE of the exact requested current ownership edges
    RETURNING the authoritative ownership facts and lifecycle carriers

    if the returned set does not certify the whole requested batch:
        ROLLBACK
        stop immediately

Q2  one bulk INSERT of DETACH_FROM lifecycle events
    using only values already returned by Q1

COMMIT
```

Q2 is never executed when Q1 does not certify the complete batch.

## Q1 responsibilities

The delete matches the requested batch against the authoritative current ownership facts using, in the M4 target model:

```text
parent_object_id
slot_declaring_template_id
slot_name
child_object_id
```

The public request supplies:

```text
parent_object_id
slot_name
child_object_ids[]
```

`slot_declaring_template_id` is read from the current persisted edge; DETACH does not resolve or reinterpret the current ObjectTemplate schema.

`DELETE ... RETURNING` should carry forward every value needed by the application and lifecycle write, including at least:

```text
child_object_id
parent_object_id
slot_declaring_template_id
slot_name
```

Canonical names may be captured in Q1 from the current parent/child Object rows when the final SQL shape does so without an additional statement. Ownership lifecycle display names remain best-effort historical labels; identifiers and persisted slot identity are the semantic facts.

## Why not force one data-modifying CTE

A one-statement form could conceptually combine:

```text
DELETE ... RETURNING
-> INSERT DETACH_FROM lifecycle rows
```

but the underlying successful work remains:

```text
delete N ownership rows
insert N lifecycle rows
```

The principal guaranteed saving is therefore one round-trip, not elimination of the substantive PostgreSQL work.

The one-statement form also makes the failure path less attractive: lifecycle rows may be staged only to be rolled back if the deleted edge count does not certify the requested batch.

The two-statement form instead stops after Q1 on an inadmissible batch.

## Complexity rule

The preferred implementation remains:

```text
simple bulk SQL
> complex SQL written only to reduce the statement counter
```

unless benchmark evidence demonstrates a material benefit from the more complex realization.

## Cost direction

Ignoring `BEGIN` / `COMMIT`, the target successful business-statement count is:

```text
DETACH = 2 statements
```

There is no warm/cold cache distinction because DETACH has no schema/cache preparation.

The number of round-trips does not grow with the number of requested child ids.

## Still open

This note does not yet freeze:

- how Q1 distinguishes missing path parent from missing/non-matching requested ownership edges without diagnostic-only round-trips;
- exact public failure codes for edge mismatch / already-absent edge;
- exact SQL shape used to carry parent/child canonical names;
- the final lifecycle bulk INSERT shape;
- final successful statement count if semantic target-existence requirements require another always-paid statement.

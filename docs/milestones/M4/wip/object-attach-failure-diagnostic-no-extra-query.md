# M4 WIP — Object ATTACH failure diagnostics without extra DB queries

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the route-local ATTACH rule that failure diagnostics must not trigger additional PostgreSQL reads solely to enrich the public error payload.

The rule applies to the current M4 batch ATTACH design:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

with body:

```json
{
  "child_object_ids": ["<child-1>", "<child-2>"]
}
```

## Frozen principle

```text
No additional PostgreSQL statement is executed only to improve diagnostics after a failure has already been determined.
```

Public diagnostics may use only:

- data already available from request parsing or previous route statements;
- route-local prepared semantic facts already held in memory;
- the known classification of the failed persistence constraint/operation;
- bounded static context that does not require another database round-trip.

They must not use:

- failure-only diagnostic SELECTs;
- re-reading current state solely to identify the exact conflicting/missing operand;
- raw PostgreSQL error text;
- SQL, table, column or constraint-name leakage in the public response.

## Concurrent child DELETE vs ATTACH

Example:

```text
preparation bulk child read
    -> child C exists

later, before Q4
    -> concurrent DELETE removes C

Q4 bulk INSERT object_components
    -> child FK to objects fails
```

The FK remains the final current-existence authority for the child operand.

M4 does **not** add child row locks solely to prevent this race and does **not** run a failure-only SELECT afterward to discover exactly which child disappeared.

The failure maps directly from the known child-reference FK failure to:

```text
HTTP 422
code = referenced_resource_not_found
```

with bounded details that do not claim knowledge not already available, for example:

```json
{
  "resource_type": "object",
  "operand": "child_object_ids"
}
```

The exact missing child id may be omitted when it is not already known without another database query.

## Why this is preferred

This keeps the route properties simple and predictable:

- no extra round-trips on failure paths;
- no diagnostic-only locking/read surface;
- persistence constraints remain the final authority for current referential validity;
- error detail precision never takes priority over mutation-path simplicity;
- public diagnostics do not overstate certainty.

## Cost impact

The frozen success-path statement counts remain unchanged:

```text
warm ATTACH batch      = 7 PostgreSQL statements + COMMIT
full-cold ATTACH batch = 9 PostgreSQL statements + COMMIT
```

There is no additional failure-only diagnostic query to count.

## Frozen takeaway

```text
Diagnose from what the route already knows.
Never query PostgreSQL again only to make the error message more specific.
```

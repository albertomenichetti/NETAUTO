# M4 WIP — Object DETACH static validation

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes zero-database validation for the M4 batch Object DETACH route.

## Public route context

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

with body:

```json
{
  "child_object_ids": ["...", "..."]
}
```

## Frozen request-shape validation

The following failures are rejected before opening the mutation Unit of Work:

```text
malformed/missing body
child_object_ids absent
child_object_ids empty
malformed UUID carrier
duplicate child_object_ids
invalid path/body transport carriers
```

Public mapping:

```text
HTTP 400
code = invalid_request
```

No PostgreSQL statement is executed for these failures.

## Self-reference

If the parent Object id appears in the requested child ids:

```text
parent_object_id in child_object_ids
```

the request is semantically invalid before the UoW.

Public mapping:

```text
HTTP 422
code = semantic_validation_failed
rule = self_reference
```

Candidate bounded detail:

```json
{
  "violations": [
    {
      "path": "child_object_ids",
      "rule": "self_reference",
      "child_object_id": "<parent_object_id>"
    }
  ]
}
```

This requires no database work because both values are already present at the transport/application boundary.

## Why retain the self-reference check for DETACH

A valid current ownership edge cannot be self-referential because the relational model retains the defensive invariant:

```text
parent_object_id <> child_object_id
```

Therefore a request asking to detach the parent from itself cannot describe a removable valid edge. Rejecting it before Q1 is both cheaper and more precise than letting it collapse into a generic ownership conflict.

## Frozen takeaway

```text
wire/static invalidity
    -> 400 invalid_request

parent included among requested children
    -> 422 semantic_validation_failed / self_reference

both paths
    -> zero PostgreSQL business statements
```

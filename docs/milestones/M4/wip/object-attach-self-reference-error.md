# M4 WIP — Object ATTACH self-reference error

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the route-local public failure semantics when the Object ATTACH batch includes the parent Object itself among `child_object_ids`.

## Frozen rule

Given:

```text
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

with:

```json
{
  "child_object_ids": ["...", "<parent_object_id>", "..."]
}
```

the request is semantically invalid before the ownership Unit of Work begins.

Public mapping:

```text
HTTP 422
code = semantic_validation_failed
```

Candidate bounded details:

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

The exact public `message` remains human-readable and non-branching.

## Why this is 422, not 409

The failure does not depend on mutable persisted ownership state.

The semantic intent itself is invalid:

```text
parent == requested child
```

Changing current ownership facts cannot make that same operand combination admissible. The caller must change the request operands.

Therefore this is a semantic validation failure, not a state conflict.

## Placement in the route

The check is performed before entering the ATTACH mutation Unit of Work.

It requires no additional PostgreSQL statement because both values are already present in the request:

```text
parent_object_id from path
child_object_ids from body
```

## Persistence defense remains

The relational ownership schema should still retain the defensive invariant:

```text
CHECK (parent_object_id <> child_object_id)
```

or equivalent constraint realization.

That persistence constraint is an invariant backstop, not the normal public validation path.

If an unexpected race/implementation defect reaches the bulk INSERT with a self-edge, the known self-reference CHECK classification can still be translated without any diagnostic reread.

## Frozen takeaway

```text
parent_object_id in child_object_ids
    -> reject before UoW
    -> HTTP 422
    -> semantic_validation_failed / self_reference
    -> zero extra DB statements
```

# M4 WIP — Object ATTACH error mapping: slot and child compatibility

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the route-local public error mapping for two ATTACH batch failures:

1. the requested component slot is unavailable in the parent Object's current exact effective schema;
2. one or more requested child Objects are semantically incompatible with the slot target lineage.

The public route under M4 discovery is:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

with batch body:

```json
{
  "child_object_ids": ["<child-1>", "<child-2>"]
}
```

## Slot unavailable

If `slot_name` is syntactically valid but does not resolve in the immutable `component_schema` facet for the parent's current exact `(template_id, template_version)` binding, ATTACH fails as a current-state conflict:

```text
HTTP 409
code = ownership_slot_unavailable
```

Candidate bounded details:

```json
{
  "parent_object_id": "<parent-object-id>",
  "slot_name": "interfaces"
}
```

Rationale:

- the path parent exists;
- the request is syntactically valid;
- slot availability depends on the parent's current exact schema binding;
- after an explicit parent SCHEMA_CHANGE, the same Object may expose a different effective component schema;
- therefore this is a mutable/current-state conflict rather than resource absence.

The existing public M1 error catalog already defines `ownership_slot_unavailable` as the ATTACH slot state-conflict code; M4 retains that classification.

## Child lineage incompatibility

If a requested child Object exists, but its stable `template_id` is not equal to or descended from the slot's `target_template_id`, the operand is semantically invalid for that slot.

Mapping:

```text
HTTP 422
code = semantic_validation_failed
```

The batch preparation already performs a bounded bulk read of requested child Objects and O(1)-shape stable ancestry lookup after cache readiness, so all incompatible children may be reported without additional database round-trips.

Candidate details:

```json
{
  "violations": [
    {
      "path": "child_object_ids",
      "rule": "incompatible_template_lineage",
      "child_object_id": "<child-object-id>",
      "template_id": "<actual-child-template-id>",
      "required_template_id": "<slot-target-template-id>"
    }
  ]
}
```

Rationale:

- the child exists;
- the current ownership state is not the reason for rejection;
- the requested child is intrinsically the wrong semantic operand for this slot target;
- making the same request succeed requires changing the operand, not waiting for a concurrency/state transition.

This matches the general public error rule that syntactically valid but semantically invalid operands map to `SEMANTIC_VALIDATION / 422`.

## Frozen distinction

```text
slot unavailable in current parent schema
    -> 409 ownership_slot_unavailable

child exists but lineage incompatible with slot target
    -> 422 semantic_validation_failed
```

This note is route-local M4 discovery input. Global API-contract reconciliation remains a later milestone-closure task.
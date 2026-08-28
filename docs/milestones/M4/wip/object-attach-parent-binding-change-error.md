# M4 WIP — Object ATTACH parent binding change error

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note records the public failure classification when Object ATTACH preparation resolves a component slot against one exact parent ObjectTemplateVersion binding, but the parent binding has changed before the protected Unit of Work stabilizes the parent row.

## Prepared versus current binding

Preparation may observe:

```text
parent.template_id      = T
parent.template_version = 4
```

and resolve the requested slot against immutable `component_schema` for `(T,4)`.

Inside the Unit of Work, after acquiring the ownership graph write gate, ATTACH locks the parent Object row with `FOR NO KEY UPDATE` and rereads the current binding.

If the current binding is instead:

```text
parent.template_id      = T
parent.template_version = 5
```

ATTACH MUST NOT continue using the slot resolution prepared for `(T,4)` and MUST NOT silently re-resolve the slot inside the same Unit of Work.

## Public outcome

The frozen M4 discovery outcome is:

```text
HTTP 409
code = concurrent_object_change
```

Candidate bounded details:

```json
{
  "object_id": "<parent_object_id>",
  "expected_template_version": 4,
  "current_template_version": 5
}
```

The caller may retry the ATTACH command. A new invocation restarts preparation from the parent current binding and resolves the requested slot against that exact immutable schema.

## Why this is not `ownership_slot_unavailable`

A binding change does not prove that the requested slot is absent in the new schema. The new exact version may still contain a semantically equivalent slot.

Therefore mapping this race to:

```text
ownership_slot_unavailable
```

would assert a fact that ATTACH has deliberately not re-evaluated.

The route-local distinction is:

```text
slot absent in the exact schema actually prepared
    -> 409 ownership_slot_unavailable

parent exact binding changed after preparation
    -> 409 concurrent_object_change
```

## No automatic in-UoW restart

M4 discovery intentionally chooses conservative failure rather than an automatic replan inside the same protected Unit of Work.

This keeps slot resolution and compatibility preparation outside the lock scope, bounds lock duration, and avoids mixing two exact-schema plans in one attempt.

## Contract handoff

`concurrent_object_change` is an M4 discovery-level candidate that is not present in the current M1 finite public error-code catalog. Milestone closure MUST reconcile the global public error catalog before implementation is authorized.

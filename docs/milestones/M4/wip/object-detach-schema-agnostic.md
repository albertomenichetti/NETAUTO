# M4 WIP — Object DETACH schema-agnostic semantics

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the route-local semantic principle that Object DETACH removes current persisted ownership facts and therefore does not need ObjectTemplate/component-schema interpretation.

## Public command context

DETACH uses the command-explicit batch-by-slot surface:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

with a non-empty duplicate-free `child_object_ids` batch and `204 No Content` on success.

The batch is atomic and non-convergent: every requested child must currently be attached through the exact requested parent/slot edge, otherwise the whole batch fails.

## Frozen semantic rule

DETACH does not decide whether a new ownership edge is admissible. It removes an already-authoritative current ownership fact.

Therefore the DETACH path does **not** need:

```text
ObjectTemplate effective component-schema resolution
target_template_id
child ObjectTemplate lineage compatibility
ObjectTemplate ancestry cache/fill
cycle detection
OWNERSHIP_GRAPH_WRITE_GATE for cycle admission
MigrationPlan/schema-change interpretation
```

No immutable-model cache lookup is required for normal DETACH semantics.

## Authoritative state

The authoritative source for DETACH is the current `object_components` edge itself.

The M4 target physical edge identity carries at least:

```text
child_object_id
parent_object_id
slot_declaring_template_id
slot_name
```

The persisted `slot_declaring_template_id` is historical/current semantic edge identity and is used directly for lifecycle emission; DETACH must not recompute it from the parent's current schema.

## Consequence for concurrent SCHEMA_CHANGE

Because DETACH does not interpret the parent's current ObjectTemplate binding, a concurrent change of `objects.template_version` does not invalidate the meaning of the ownership edge being removed.

Therefore DETACH does not require the ATTACH-style parent schema-stability protocol merely to preserve slot interpretation.

Any lock retained in the final DETACH Unit of Work must have a concrete ownership-state or lifecycle correctness purpose; it must not be inherited mechanically from ATTACH.

## No unlocked semantic preparation

There is no separate unlocked semantic preparation phase for DETACH.

The command can enter its mutation Unit of Work directly and arbitrate against current ownership rows.

This intentionally differs from ATTACH, where preparation resolves immutable schema semantics and lineage compatibility before mutation.

## Frozen takeaway

```text
ATTACH
    -> creates new edge
    -> schema + compatibility + cycle admission required

DETACH
    -> removes current edge
    -> current object_components facts are authoritative
    -> no schema/cache/ancestry/cycle preparation
```

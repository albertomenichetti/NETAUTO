# M4 — Object.DETACH discovery

**Status:** WIP / NON-NORMATIVE

## Scope

First-phase M4 discovery for `Object.DETACH`, assuming the candidate richer current ownership fact discussed in the Object/components discovery:

```text
object_components
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name
```

This note deliberately does not redesign locking/concurrency.

## Current AS-IS

The current flow stabilizes the parent Object, loads parent and child, loads the child's current ownership fact, and treats an absent edge as idempotent success. If a current edge exists it requires the requested parent and `slot_name` to match, then loads the parent's exact effective ObjectTemplate schema only to resolve the semantic slot and recover `slot_declaring_template_id` for validation/projection/lifecycle metadata. It then deletes the ownership fact and emits the DETACH lifecycle event.

Because current `object_components` stores only `slot_name`, the semantic slot identity must be reconstructed from the parent's current exact schema.

## Finding: materialized semantic slot identity removes the model read

With the richer ownership fact, the exact current edge already contains:

```text
slot_declaring_template_id
slot_name
```

Therefore DETACH does not need:

- ObjectTemplate effective-schema loading;
- DataType/runtime-property loading;
- ObjectTemplate ancestry;
- slot-target compatibility checks;
- cycle checks.

The operation removes a current fact and cannot introduce an ownership cycle or a new compatibility dependency.

## Candidate data path

```text
load/stabilize current ownership for child

none
    -> idempotent success

edge exists
    -> require requested parent matches edge.parent_object_id
    -> require requested semantic edge matches
       edge.slot_declaring_template_id + edge.slot_name

load only current parent/child metadata required by the lifecycle event

DELETE exact current edge

INSERT DETACH event using the semantic slot identity already carried by the edge

COMMIT
```

The exact SQL predicate may include all stabilized edge fields even though `child_object_id` remains the physical primary key:

```text
child_object_id
parent_object_id
slot_declaring_template_id
slot_name
```

## Architectural delta candidate

The current architecture says that a real DETACH resolves the semantic slot against the current parent effective schema and treats failure to resolve it as invariant corruption.

M4 candidate direction:

> ATTACH owns strong slot/compatibility admission. DETACH operates on the already admitted current ownership fact and does not re-certify the parent schema solely to remove that fact.

This mirrors the broader M4 principle that removals should not repeat semantic admission checks that cannot make the removal safer.

## Cache/materialization consequences

No worker cache is required by DETACH once semantic slot identity is persisted on the ownership edge.

The edge itself carries the semantic identity required for:

- exact current-fact matching;
- lifecycle metadata;
- public ownership projection.

The current parent ObjectTemplate schema remains relevant to ATTACH and SCHEMA_CHANGE, not to DETACH admission.

## Open

- exact concurrency/liveness protocol;
- precise public command matching semantics if a future API exposes declaring-template identity explicitly;
- final relational constraints/indexes for the richer `object_components` row.

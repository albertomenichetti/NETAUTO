# M4 WIP — Object SCHEMA_CHANGE prepared candidate

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the final output of optimistic preparation for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

It is intentionally caller-side and route-local. It does not change the already-frozen UoW/concurrency rules.

## Input state

Before a successful `PreparedSchemaChange` can be built, the command has already obtained:

```text
MigrationPlan[(template_id, source_version, target_version)] READY

coherent Object aggregate snapshot S
    Object intrinsic state
        id
        canonical_name
        template_id
        template_version
        properties

    current attached ownership edges where Object is parent
        child_object_id
        slot_declaring_template_id
        slot_name

expected_object_fingerprint
    SHA-256(canonical_json(S))
```

The Object binding observed in `S` has already been checked to match the source binding used to select/compile the MigrationPlan. A mismatch terminates the request conservatively; no automatic re-plan occurs inside the same request.

## Preparation work already completed

Using only `S` plus the immutable `MigrationPlan`, outside the mutation UoW:

```text
property migration
    S.properties
    + MigrationPlan.property_rules
    -> target_properties

component/ownership admission
    S.current_attached_ownership_edges
    + MigrationPlan.component_rules
    -> success or semantic blocker
```

No ObjectTemplate schema reinterpretation, child-Object read, DataType read, cache fill or database lock is performed during this stage.

If property migration or component admission fails, the request terminates before entering the mutation UoW.

## PreparedSchemaChange

A successful optimistic preparation produces one immutable per-request candidate conceptually equivalent to:

```text
PreparedSchemaChange
    object_id
    canonical_name

    template_id
    source_version
    target_version

    expected_object_fingerprint

    target_properties

    lifecycle_before
    lifecycle_after
```

`canonical_name` is carried explicitly because it participates in the intrinsic Object snapshot and in the lifecycle before/after states.

## Lifecycle snapshots

The lifecycle payload is fully built during preparation from the coherent source snapshot and the prepared target state.

```text
lifecycle_before
    id                 = S.id
    canonical_name     = S.canonical_name
    template_id        = S.template_id
    template_version   = source_version
    properties         = S.properties

lifecycle_after
    id                 = S.id
    canonical_name     = S.canonical_name
    template_id        = S.template_id
    template_version   = target_version
    properties         = target_properties
```

Ownership/components are deliberately excluded from the intrinsic historical Object lifecycle snapshot; ATTACH/DETACH have their own lifecycle facts.

## UoW handoff invariant

The mutation UoW receives a mechanically applicable candidate.

It must not redo expensive semantic preparation.

Conceptually, after protected current-state checks succeed, the UoW consumes:

```text
target_version
target_properties
lifecycle_before
lifecycle_after
```

The candidate remains valid for commit only if the protected fresh Object aggregate fingerprint equals:

```text
PreparedSchemaChange.expected_object_fingerprint
```

A mismatch means the optimistic preparation is stale and is handled by the separately frozen bounded fingerprint-retry policy.

## Frozen decision

```text
successful optimistic preparation
    -> one PreparedSchemaChange

PreparedSchemaChange contains all state required for the eventual Object mutation
and SCHEMA_CHANGE lifecycle insert.

No semantic migration/revalidation is intentionally deferred into the short UoW.
```

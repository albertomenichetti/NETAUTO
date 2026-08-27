# M4 — Object component read projections discovery

**Status:** WIP / NON-NORMATIVE

## Scope

This note captures the M4 discovery result for current ownership read projections after enriching the runtime ownership fact with semantic slot identity.

Candidate runtime edge shape:

```text
object_components
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name
```

`slot_declaring_template_version` is intentionally not persisted. Current ownership identity is the stable semantic slot key `(slot_declaring_template_id, slot_name)`; the parent Object's current exact ObjectTemplateVersion supplies the current exact slot contract when an operation needs it.

## AS-IS problem

Current `components` and `owner` projections persist only `slot_name` on `object_components`. To return the mandatory public `slot_declaring_template_id`, persistence reconstructs the parent Object's exact ObjectTemplate inheritance chain using recursive SQL and searches exact component declarations for that name.

This makes pure current-fact reads depend on ObjectTemplate model reconstruction solely because the runtime ownership edge is under-materialized.

## Candidate M4 direction

With `slot_declaring_template_id` persisted on the current edge:

- `LIST components` becomes a one-statement projection rooted at the parent Object and a paged `object_components` relation;
- `GET owner` becomes a one-statement child Object `LEFT JOIN object_components` projection;
- no ObjectTemplateVersion traversal, effective-schema load, DataType read, ancestry check, cache lookup or semantic recertification is needed;
- PostgreSQL remains the sole authority for current mutable ownership facts.

### LIST components

The result already exists directly on the edge:

```text
slot_declaring_template_id
slot_name
child_object_id
```

The statement should retain the existing distinction between parent 404, existing parent with an empty page, and existing parent with page rows.

### GET owner

The child-object PK lookup combined with the `object_components.child_object_id` PK naturally distinguishes child 404, detached child (`owner = null`) and owned child.

## Index note

The existing access path:

```text
ix_object_components_parent_slot_child
    (parent_object_id, slot_name, child_object_id)
```

already matches parent navigation, optional slot-name filtering and child-id keyset pagination. Adding `slot_declaring_template_id` does not by itself justify a new index. Whether it should be an included column is a later PostgreSQL physical-plan question, not an architectural requirement.

## Working conclusion

`Object.components` and `Object.owner` should become pure current-fact projections. Materializing stable semantic slot identity at ATTACH time removes the recursive exact-ObjectTemplate traversal from both reads and reinforces the general M4 rule: interpret model semantics on mutation/admission paths and persist the resolved stable identity needed by hot runtime consumers.

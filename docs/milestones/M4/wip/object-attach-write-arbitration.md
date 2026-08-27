# M4 WIP — Object ATTACH write arbitration

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the current-owner and relational-arbitration direction for the M4 TO-BE batch ATTACH operation:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

with a non-empty list of `child_object_ids`.

## No current-owner preliminary read

ATTACH does not pre-read `object_components` merely to classify whether each requested child is already owned.

The preparatory child bulk read is limited to current Object facts needed for semantic admission, primarily:

```text
child.id
child.template_id
child.canonical_name   # lifecycle/display metadata if required
```

Current ownership is intentionally left to the final relational write arbitration.

## Existing ownership semantics

The earlier candidate "identical edge converges successfully" is superseded.

The frozen M4 direction is deliberately stricter and simpler:

```text
requested child has no current owner
    -> eligible for insertion

requested child already has ANY current owner
    -> INSERT conflicts
    -> entire ATTACH batch fails/rolls back
```

This includes the case where the existing edge is exactly identical to the requested parent/semantic slot.

Therefore ATTACH is not idempotent with respect to an already-persisted edge.

## PostgreSQL authority

Candidate ownership table remains one-owner shaped:

```text
object_components
    child_object_id              PK
    parent_object_id             NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
```

The relational model directly owns the important final arbitration:

```text
PK(child_object_id)
    -> at most one current owner
    -> any already-owned requested child causes write conflict

FK(parent_object_id -> objects.id)
    -> parent lifetime protection at write time

FK(child_object_id -> objects.id)
    -> child lifetime protection at write time

CHECK(parent_object_id <> child_object_id)
    -> no self edge
```

A bulk ATTACH can therefore attempt all requested edge INSERTs inside one transaction. Any relational failure causes rollback of the whole atomic batch.

No application-side second owner SELECT is required merely to re-prove these relational invariants.

## Parent lock purpose

An explicit parent Object concurrency lock is still required, but not primarily for parent lifetime. Parent lifetime is already protected by the FK when the edge is written.

The parent lock protects the semantic relationship between:

```text
parent.template_id / parent.template_version
+
resolved effective slot
+
new outgoing ownership edges
```

Preparation resolves `slot_name` against the parent's exact current OTV, usually from the immutable `component_schema` cache facet.

Without parent stabilization, the following race would be possible:

```text
prepare against parent exact OTV V1
resolve slot S on V1

concurrent SCHEMA_CHANGE commits V1 -> V2
where S is removed/replaced/incompatible

ATTACH inserts edge prepared for V1
```

All PK/FK constraints could still succeed while the committed ownership edge is semantically invalid under V2.

Therefore ATTACH and parent SCHEMA_CHANGE must rendezvous on the parent Object concurrency owner.

## Preparation vs protected mutation

Current direction:

```text
PREPARATION, unlocked
    1. read parent current exact binding
    2. resolve requested slot cache-first from exact component_schema
    3. bulk-read all requested child Objects
    4. validate parent != child in application as cheap early rejection
    5. verify every child stable lineage is compatible with slot target
       using StableObjectTemplateAncestryCache

MUTATION UoW
    6. lock/stabilize parent Object
    7. ensure parent binding still matches the exact binding used for preparation
    8. perform ownership-cycle protection/check under the final M4 protocol
    9. bulk INSERT all requested object_components edges
       - any PK/FK/CHECK/error -> rollback complete batch
    10. insert ATTACH lifecycle rows for the inserted edges
    11. commit once
```

The exact parent lock statement/mode and exact cycle-add gate realization remain to be frozen during the continuing route-local concurrency pass.

## False-success / false-failure posture

The design continues the M4 priority:

```text
false success
    -> prevent strongly

conservative false failure
    -> acceptable where it cannot create incoherent state
```

Using relational write arbitration avoids false success from stale preliminary owner observations. If a requested child is already owned when the INSERT is arbitrated, the batch fails atomically.

## Implications

- no current-owner cache;
- no owner pre-read;
- no owner re-read;
- no special identical-edge convergence path;
- no N application-level ownership classifications;
- one atomic bulk-write attempt for the batch;
- PK/FK/CHECK constraints are first-class concurrency/safety authorities rather than merely backup validation.

# M4 WIP — Object ATTACH write arbitration

Status: RECONCILED DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note records the final ownership-arbitration split for the M4 TO-BE batch ATTACH operation.

The complete route authority is `to-be-api-object-attach-batch.md`.

## No preliminary owner read

ATTACH does not read current ownership during unlocked preparation.

The preparatory child bulk read is limited to:

```text
child.id
child.template_id
child.canonical_name
```

This avoids stale mutable owner observations outside the protected graph state.

## Protected Q3 ownerlessness admission

Current ownerlessness is nevertheless checked before persistence, but only inside Q3 after `OWNERSHIP_GRAPH_WRITE_GATE` and parent stabilization have been acquired.

One protected statement returns:

```text
has_owned_requested_child
root_is_requested
```

Therefore:

```text
any requested child currently owned
    -> 409 ownership_conflict

otherwise root(parent) requested
    -> 409 ownership_cycle

otherwise
    -> proceed to bulk INSERT
```

This Q3 read is required for graph admission and public conflict/cycle distinction; it is not a diagnostic-only query.

## Existing ownership semantics

M4 supersedes identical-edge convergence.

```text
requested child currently ownerless
    -> may proceed to Q4

requested child has ANY current owner
    -> ownership_conflict
    -> whole batch fails
```

This includes an existing edge that is exactly identical to the requested parent and semantic slot.

## Q4 relational authority

Candidate ownership table remains:

```text
object_components
    child_object_id              PK
    parent_object_id             NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
```

Q4 is one bulk INSERT with no `ON CONFLICT`.

Relational responsibilities:

```text
PK(child_object_id)
    -> final at-most-one-owner authority
    -> closes residual ownership races at the actual write

FK(parent_object_id -> objects.id)
FK(child_object_id -> objects.id)
    -> final parent/child lifetime authority

CHECK(parent_object_id <> child_object_id)
    -> self-edge backstop
```

Any constraint failure aborts the statement and rolls back the whole atomic batch.

Q3 and Q4 therefore have complementary responsibilities rather than duplicating authority:

```text
Q3
    -> fresh protected mutable graph admission
    -> owner-conflict classification
    -> transitive cycle certification

Q4 constraints
    -> final persisted single-owner/lifetime/direct-integrity arbitration
```

## Parent lock purpose

The parent Object is locked `FOR NO KEY UPDATE` after the graph gate.

This is primarily semantic stabilization, not lifetime protection. It prevents parent SCHEMA_CHANGE from changing the exact governing schema after preparation has resolved the requested slot.

Q2 rereads and compares the exact `(template_id, template_version)` binding. Mismatch fails conservatively with `concurrent_object_change`; there is no in-lock slot re-resolution.

## Final sequence

```text
PREPARATION, unlocked
    1. read parent exact binding + canonical_name
    2. resolve slot cache-first
    3. bulk-read child Object facts only
    4. reject self-reference
    5. resolve stable-lineage compatibility through ancestry cache

MUTATION UoW
    6. acquire graph edge-add gate
    7. lock parent / verify prepared binding
    8. Q3 ownerlessness + root-only cycle admission
    9. Q4 bulk INSERT object_components
    10. Q5 bulk INSERT ATTACH_TO lifecycle rows
    11. commit once
```

No application-side owner pre-read/re-read exists outside the protected Q3 statement, and no diagnostic-only DB read is allowed after an error.

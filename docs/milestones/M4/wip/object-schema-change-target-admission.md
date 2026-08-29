# M4 WIP — Object SCHEMA_CHANGE target admission

Status: SUPERSEDED SOURCE MATERIAL / M4 WIP / NON-NORMATIVE GLOBALLY

## Current supersession notice

This file is retained only as historical/source evidence for the target-admission exploration of:

```http
POST /api/v1/core/objects/{object_id}/schema
```

Current authority is [`object-schema-change.md`](object-schema-change.md), together with the reviewed cross-operation owners it references.

The current full sweep has superseded several central conclusions below:

```text
forward-only / target_version > source_version admission
    -> superseded by exact-target migration semantics

standalone PRELIMINARY TARGET ADMISSION query
    -> superseded
    -> requested TARGET existence/status may be observed in the same STEP-1
       PostgreSQL statement as the current intrinsic Object generation

TARGET disappearance at final admission -> stale/lifetime retry
    -> superseded
    -> distinct TARGET absence maps normally to
       422 referenced_resource_not_found
    -> only stale objects.revision is intrinsic automatic-retry control flow
```

Retained conceptual evidence:

```text
distinct TARGET is a referenced command operand
real new binding requires exact TARGET PUBLISHED through commit
early TARGET status observation never authorizes success
cached immutable TARGET semantics do not prove current lifecycle admission
final protected TARGET admission is the new-binding lifecycle authority
existing but DRAFT/DEPRECATED TARGET -> dependency_not_admissible
```

Everything below is historical context and must not override the current owner.

---

## Historical context

The earlier route model treated the requested exact ObjectTemplateVersion as a referenced command operand and a lifecycle-sensitive new binding target.

It split target admission into two levels:

```text
PRELIMINARY TARGET ADMISSION
    unlocked
    cheap failure filtering before expensive cache/fill/migration work

FINAL TARGET ADMISSION
    inside short mutation UoW
    exact target row protected through commit
    strong false-success prevention
```

The preliminary observation was never intended as correctness authority for successful commit.

### Historical preliminary outcomes

For a distinct exact target:

```text
target exact OTV absent
    -> 422 referenced_resource_not_found

target exact OTV exists but DRAFT/DEPRECATED
    -> 409 dependency_not_admissible

target exact OTV PUBLISHED
    -> semantic preparation may continue
```

The historical design allowed an unlocked preliminary observation to produce a conservative false failure if target lifecycle changed concurrently. That general principle remains compatible with the current design, but the separate query is no longer required: the same information may be carried by STEP 1 without another round trip.

### Immutable semantic knowledge

Once an exact OTV has been published, its semantic payload is immutable even if its lifecycle later becomes `DEPRECATED`.

Therefore a cached exact closure or `MigrationPlan` remains immutable semantic knowledge and must never be treated as current new-binding lifecycle authority.

### Current final admission rule

For a real `SOURCE != TARGET` migration, the current owner requires final protected exact TARGET admission through commit:

```text
TARGET exists + PUBLISHED
    -> may proceed while protected

TARGET exists + DRAFT/DEPRECATED
    -> 409 dependency_not_admissible

TARGET absent
    -> 422 referenced_resource_not_found
```

The equal-target semantic no-op is different:

```text
TARGET == current SOURCE
    -> 204
    -> no new binding
    -> no TARGET PUBLISHED re-admission
```

Final TARGET absence is not a revision retry trigger. The intrinsic retry protocol is owned exclusively by stale `objects.revision` in the current SCHEMA_CHANGE owner.

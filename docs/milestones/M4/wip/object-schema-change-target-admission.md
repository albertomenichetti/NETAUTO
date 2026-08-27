# M4 WIP — Object SCHEMA_CHANGE target admission

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the target-version existence/lifecycle admission semantics frozen for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

The route is an explicit forward ObjectTemplateVersion migration. The path resource is the Object; the requested exact ObjectTemplateVersion is a referenced command operand and a lifecycle-sensitive new binding target.

## Admission ordering

After reading the preparatory Object aggregate snapshot `S`, the command first classifies forwardness:

```text
source_version = S.template_version

target_version <= source_version
    -> semantic_validation_failed / 422
    -> no target admission work
    -> no mutation UoW

target_version > source_version
    -> continue to target admission
```

Target admission is deliberately split into two levels:

```text
PRELIMINARY TARGET ADMISSION
    unlocked
    cheap failure filtering before expensive cache/fill/migration work

FINAL TARGET ADMISSION
    inside short mutation UoW
    exact target row protected through commit
    strong false-success prevention
```

The preliminary check is not a correctness authority for success.

## Preliminary unlocked target check

The preparatory phase performs one minimal exact lookup using the Object's stable template lineage:

```text
(template_id = S.template_id, version = requested target_version)
    -> existence
    -> current lifecycle status
```

No ObjectTemplate default/latest/highest selector participates.

### Target exact version absent

The requested exact OTV is a referenced operand rather than the path resource.

Therefore:

```text
target exact OTV absent
    -> SEMANTIC_VALIDATION / 422
    -> code = referenced_resource_not_found
```

Bounded details identify the referenced exact version, conceptually:

```json
{
  "resource_type": "object_template_version",
  "id": "<template-id>",
  "version": 6
}
```

### Target exact version exists but is not PUBLISHED

A new Object binding may target only an exact `PUBLISHED` ObjectTemplateVersion.

Therefore:

```text
status = DRAFT
or
status = DEPRECATED
    -> STATE_CONFLICT / 409
    -> code = dependency_not_admissible
```

### Target exact version is PUBLISHED

The command may continue with immutable semantic preparation:

```text
load/fill SOURCE effective schema
load/fill TARGET effective schema
obtain/build immutable MigrationPlan(source,target)
apply plan to Object snapshot S
build/validate/canonicalize complete PreparedSchemaChange
```

The preliminary PUBLISHED observation does not authorize commit.

## Conservative preliminary failures

The unlocked preliminary lookup is intentionally allowed to produce conservative stale failures.

Example:

```text
T1 sees target DRAFT
T2 publishes target
T1 may still return 409 dependency_not_admissible
```

This is acceptable because it cannot create incoherent persisted state. A caller retry observes fresh state.

Likewise, an exact target observed absent may be created/published later; the request may still return its failure from the snapshot it actually inspected.

The protocol priority remains:

```text
false failure
    -> acceptable

false success
    -> must be prevented strongly
```

## Immutable semantic knowledge survives later deprecation

Once an exact OTV has been published, its semantic payload is immutable even if its lifecycle later becomes `DEPRECATED`.

Therefore a target that was PUBLISHED during preparation may legitimately have its immutable effective schema and source->target `MigrationPlan` loaded or retained in cache even if it becomes DEPRECATED before final admission.

Lifecycle deprecation changes only current admission of new bindings. It does not invalidate immutable semantic cache entries or the meaning of an already-built MigrationPlan.

## Final strong target admission inside the UoW

A successful prepared candidate enters the short mutation UoW.

The first model-plane protection step is conceptually:

```sql
SELECT status
FROM object_template_versions
WHERE template_id = :template_id
  AND version = :target_version
FOR SHARE;
```

The exact identity is selected independently of status so the command can distinguish an existing-but-inadmissible target from an unexpected missing target.

### Row exists and status is PUBLISHED

```text
TARGET OTV @ FOR SHARE
status == PUBLISHED
    -> final target admission succeeds
    -> SHARE hold remains through commit
```

This is the strong success authority.

The hold rendezvous with target lifecycle mutation and prevents target `DEPRECATE` from completing while this transaction is creating the new Object->OTV binding.

### Row exists but status is no longer PUBLISHED

For example, preparation observed PUBLISHED but target deprecation won before Q1:

```text
Q1 returns target row
status = DEPRECATED
    -> dependency_not_admissible / 409
    -> rollback
```

No fingerprint/Object lock work is required after this final target-admission failure.

### Target row unexpectedly missing at final admission

An exact PUBLISHED version is not individually deletable under the normal lifecycle contract. Therefore disappearance between successful preparation and final Q1 indicates a broader lifetime race/stale preparation rather than a normal exact-version operand classification.

Frozen handling direction:

```text
preparation previously observed admissible target
Q1 unexpectedly finds no exact target row
    -> do not immediately expose a newly invented target-not-found result
    -> treat as stale/lifetime race
    -> rollback
    -> bounded restart from fresh preparation
```

A fresh restart then classifies the authoritative current situation, including path-Object absence if a concurrent lifetime mutation removed it.

## Separation of responsibilities

```text
PRELIMINARY unlocked check
    -> cheap early rejection
    -> protects CPU/cache-fill cost
    -> conservative false failure allowed
    -> never authorizes success

FINAL Q1 @ FOR SHARE
    -> current exact target lifecycle authority
    -> must observe PUBLISHED
    -> protects PUBLISHED through commit
    -> prevents false success strongly
```

No cache entry is authority for current lifecycle status.

## Frozen decision

```text
Object snapshot S exists
+
target_version > S.template_version

PRELIMINARY exact target lookup, unlocked
    absent
        -> 422 referenced_resource_not_found

    DRAFT / DEPRECATED
        -> 409 dependency_not_admissible

    PUBLISHED
        -> perform immutable semantic preparation

UoW Q1 exact TARGET OTV @ FOR SHARE
    PUBLISHED
        -> hold through commit
        -> proceed to Object concurrency-owner lock

    existing but non-PUBLISHED
        -> 409 dependency_not_admissible
        -> rollback

    unexpectedly absent after prior successful preparation
        -> stale/lifetime race
        -> rollback + bounded restart
```

This split minimizes wasted expensive preparation while making the final commit depend only on a strongly protected current target admission.
# M4 WIP — Object SCHEMA_CHANGE target admission lock

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note freezes the first statement inside the short mutation UoW for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

## Q1 — exact target ObjectTemplateVersion admission

After optimistic preparation has produced a complete `PreparedSchemaChange`, the command begins the mutation UoW and first locks the exact target ObjectTemplateVersion.

Conceptual SQL:

```sql
SELECT status
FROM object_template_versions
WHERE template_id = :template_id
  AND version = :target_version
FOR SHARE;
```

The query is by exact identity, not by `status = 'PUBLISHED'`, because the caller-visible failure class depends on distinguishing exact target absence from a target that exists but is not currently admissible.

## Outcomes

```text
0 rows
    -> exact target version no longer exists
    -> fail / rollback according to the route's final failure mapping

status = DRAFT
    -> dependency_not_admissible / 409

status = DEPRECATED
    -> dependency_not_admissible / 409

status = PUBLISHED
    -> continue
    -> retain FOR SHARE lock until COMMIT/ROLLBACK
```

## Why PostgreSQL is mandatory here

`MigrationPlanCache[(template_id, source_version, target_version)]` may already be READY and remain semantically correct even if the target later transitions from `PUBLISHED` to `DEPRECATED`.

The cache therefore proves immutable source/target semantics only. It cannot prove current new-binding admission.

Current target lifecycle state remains PostgreSQL authority.

Example:

```text
MigrationPlanCache[(Server, 4, 5)] = HIT

concurrent model mutation:
    Server v5 PUBLISHED -> DEPRECATED

MigrationPlan 4 -> 5 remains semantically valid
but a new Object binding to v5 is no longer admissible
```

Q1 therefore rechecks current status inside the UoW and holds the exact target row with `FOR SHARE` through commit so a concurrent deprecation cannot make the target non-admissible after the successful check but before the Object mutation commits.

## UoW ordering

Frozen route-local order begins:

```text
BEGIN

Q1
    exact TARGET ObjectTemplateVersion
    SELECT status ... FOR SHARE
    require PUBLISHED
    hold through commit

Q2
    parent Object concurrency-owner lock
    [next discovery step]
```

The exact target model row is acquired before the Object row, preserving the current global lock-order direction of model-plane dependency rows before data-plane Object rows.

## Cache authority boundary

```text
cache
    -> immutable exact semantics
    -> MigrationPlan

PostgreSQL Q1
    -> current exact target existence
    -> current PUBLISHED admission
    -> lifecycle stability through commit
```

No semantic reconstruction, cache fill or expensive model-plane work is allowed while Q1's admission lock is held; all such work was completed during optimistic preparation.

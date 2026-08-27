# M4 WIP — Object SCHEMA_CHANGE removes standalone preliminary target admission

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note supersedes the earlier route-local decision that required a dedicated unlocked preliminary exact-target existence/status lookup before immutable migration preparation for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

## Superseded shape

Earlier discovery split target admission into:

```text
PRELIMINARY unlocked exact target lookup
    -> existence/status
    -> reject absent / DRAFT / DEPRECATED early

FINAL UoW Q1
    -> exact target ObjectTemplateVersion @ FOR SHARE
    -> require PUBLISHED through commit
```

The preliminary lookup was never a correctness authority. Its only purpose was to avoid spending cache-fill / migration-preparation work for a target that would later fail final admission.

## Updated decision

The standalone preliminary target-admission query is removed.

The normal caller-side sequence becomes:

```text
1. read Object binding
       -> template_id
       -> source_version

2. require requested target_version > source_version

3. obtain/build MigrationPlanCache[(template_id, source_version, target_version)]
       -> use cached immutable inputs where available
       -> cold-fill missing immutable inputs where necessary

4. read complete Object aggregate
       -> verify binding still matches the source used by MigrationPlan
       -> compute expected aggregate fingerprint
       -> prepare migration candidate

5. enter mutation UoW

6. Q1 exact TARGET OTV @ FOR SHARE
       -> current PostgreSQL admission authority
       -> must be PUBLISHED
       -> SHARE held through commit
```

## Rationale

The route is expected to receive an explicit migration request toward a target version deliberately selected by an operator/caller. A concurrent target deprecation during the same short request is expected to be rare.

Paying one unconditional PostgreSQL round-trip on every successful migration solely to pre-filter that rare race is not justified because the final UoW already protects correctness strongly.

A stale immutable `MigrationPlan` or cached exact target semantics cannot create a false success:

```text
target semantic cache / MigrationPlan remains immutable and valid
+
target later becomes DEPRECATED

-> preparation may perform some now-useless CPU/cache work
-> UoW Q1 observes DEPRECATED
-> mutation is rejected
-> no new Object binding is committed
```

The trade-off is therefore:

```text
remove one DB round-trip from every normal warm request
+
accept rare wasted preparation work if target admission changes concurrently
```

This is consistent with the M4 priority:

```text
false success -> prevent strongly
rare wasted work / conservative failure -> acceptable
```

## Cache-hit behavior

If the required MigrationPlan and immutable semantic inputs are already READY:

```text
no target lifecycle/status query is performed during preparation
```

Current target lifecycle is checked only by final UoW Q1.

Exact DataTypeVersion semantics remain usable from cache regardless of later `PUBLISHED -> DEPRECATED` transitions because exact semantic payload is immutable. This decision concerns target ObjectTemplateVersion new-binding admission, not DataType semantic validity.

## Cold target-closure behavior

If the MigrationPlan is missing and the exact TARGET ObjectTemplate closure must be cold-loaded, the existing full-closure loader requirement already anchors the read to `object_template_versions` so that a semantically empty effective schema can be distinguished from a nonexistent exact version.

Therefore the same bounded bulk closure-load statement may incidentally observe exact target existence/status while loading missing immutable materialization; no dedicated preliminary target-admission query is added.

Conceptually:

```text
TARGET closure cache MISS
    -> bulk exact-closure load anchored by exact OTV identity

exact target absent
    -> loader cannot produce exact immutable target closure
    -> route classifies referenced target absence

exact target DRAFT
    -> no immutable PUBLISHED/DEPRECATED materialized closure exists
    -> route classifies target as inadmissible

exact target PUBLISHED or DEPRECATED
    -> immutable materialized semantic closure may be loaded/cached
    -> current new-binding admission is still decided only by UoW Q1
```

A DEPRECATED exact target may therefore have perfectly valid immutable semantics and a reusable cached MigrationPlan while still being rejected for a new Object binding by Q1.

## Strong final admission remains unchanged

The successful mutation still requires:

```sql
SELECT status
FROM object_template_versions
WHERE template_id = :template_id
  AND version = :target_version
FOR SHARE;
```

and:

```text
status == PUBLISHED
```

The lock remains held through Object mutation + lifecycle persistence + commit.

Therefore removing preliminary admission does not weaken target-binding correctness or lifecycle concurrency guarantees.

## Frozen decision

```text
standalone preliminary target existence/status query
    -> REMOVED

immutable target semantic cache / MigrationPlan
    -> may be consumed before current lifecycle admission

cold exact-closure load
    -> may classify absent/DRAFT as part of the same bounded loader statement
    -> no extra preliminary round-trip

final target admission authority
    -> PostgreSQL UoW Q1 exact OTV @ FOR SHARE
    -> require PUBLISHED through commit
```

This note supersedes the earlier preliminary-admission portion of `object-schema-change-target-admission.md`; its final strong Q1 admission semantics remain in force.

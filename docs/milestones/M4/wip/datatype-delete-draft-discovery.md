# M4 — DataType DELETE_DRAFT discovery

**Status:** WIP / NON-NORMATIVE

**Role:** bounded discovery note for `DataType.DELETE_DRAFT`. This document records AS-IS evidence, findings and working hypotheses only. It does not define the M4 contract, TO-BE architecture, persistence schema, cache contract or concurrency realization.

The delivered AS-IS under `docs/architecture/` remains authoritative until M4 explicitly freezes a TO-BE delta.

## 1. AS-IS flow

Current `DELETE_DRAFT(datatype_id, version, expected_revision)` performs, inside one write UoW:

```text
lock DataType header      FOR NO KEY UPDATE
lock exact DataTypeVersion FOR UPDATE
load exact DataTypeVersion
verify status == DRAFT
verify revision == expected_revision
DELETE exact DataTypeVersion
COMMIT
```

The successful path therefore uses two locking reads, one ordinary exact-version read and one DELETE statement.

## 2. Cacheability

The exact DRAFT state is intentionally not part of the immutable worker-local semantic cache:

```text
status
revision
constraints
```

are current mutable state, and the DRAFT may be revised, deleted and — when the highest DRAFT is removed — its version number may later be reused according to current version-allocation semantics.

Therefore `DELETE_DRAFT` has no useful dependency on the immutable semantic cache during admission.

## 3. Data-access finding

The exact-version locking read and the following ordinary exact-version SELECT both address the same current row. The operation needs only the protected current carriers required for admission:

```text
status
revision
```

Working M4 direction, without changing the current locking contract:

```text
locking read of exact DRAFT
    -> return status + revision
    -> validate DRAFT + expected_revision
    -> DELETE
```

This could remove the ordinary post-lock exact-version read while preserving the same current-state authority and row-lock structure.

## 4. Deferred concurrency question

The current stable-header lock also participates in same-lineage version-set and aggregate-lifetime coordination. Whether it can be changed or absorbed into another mechanism is deliberately deferred to the later global concurrency redesign phase.

In particular, the relationship between `DELETE_DRAFT` and `CREATE_NEXT` is semantically relevant because deleting the highest DRAFT can change the next allocated version number.

No local locking change is proposed by this discovery note.

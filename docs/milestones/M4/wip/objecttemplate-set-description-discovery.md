# ObjectTemplate SET_DESCRIPTION discovery

> WIP / NON-NORMATIVE. Discovery notes only; not an implementation contract.

## Scope

Audit of `ObjectTemplate.SET_DESCRIPTION` during M4 design discovery. Lock redesign remains deferred to the later global concurrency phase.

## Current semantic role

`description` is mutable, non-semantic lineage metadata. It does not participate in ObjectTemplate inheritance, exact-version semantics, effective-schema construction, validation, lifecycle admission, or runtime Object validation.

## AS-IS data path

The application currently acquires an ObjectTemplate header `NO KEY UPDATE` lock and then calls persistence `set_description()`. Persistence already performs a single `UPDATE object_templates ... RETURNING object_templates` statement and returns the updated lineage.

Ignoring commit, the current path is therefore:

1. explicit header locking read;
2. `UPDATE ... RETURNING`.

## M4 findings

### No cache or materialization role

`description` must remain outside any stable semantic lineage cache and outside immutable exact-version/runtime caches. Updating it must not invalidate:

- stable lineage ancestry materialization;
- immutable effective-schema materializations;
- immutable ObjectTemplate runtime cache entries.

### Candidate data path

At the data-access level, the natural target is a single statement:

```sql
UPDATE object_templates
SET description = :description
WHERE id = :template_id
RETURNING *;
```

The explicit header lock is not justified or removed in this first audit phase. Whether it is redundant with PostgreSQL's row lock acquired by the `UPDATE`, and how the mutation must rendezvous with `DELETE_LINEAGE` or other concurrent model-plane operations, must be rederived in the later global concurrency phase.

## Preliminary conclusion

`ObjectTemplate.SET_DESCRIPTION` is already minimal at the persistence layer. M4 should preserve `description` as mutable non-semantic metadata, exclude it from semantic caches/materializations, and use `UPDATE ... RETURNING` as the baseline data path. Any explicit pre-lock requirement remains an open concurrency question rather than a data-access requirement.
